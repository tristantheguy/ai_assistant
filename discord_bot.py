# Discord Bot for AI Assistant Project
# Application ID: 311019517365190656
# Public Key: acf2dda637df5e9d50726ab5c4b886eb9e9b616927ba209afbaf54b449b067be

import os
import threading
import time

import discord
from llm_client import OllamaClient
from system_monitor import SystemMonitor

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # allow reading message text
client = discord.Client(intents=intents)
llm = OllamaClient()
monitor = SystemMonitor()

_monitor_thread = None
_stop_event = threading.Event()


def _monitor_loop():
    while not _stop_event.is_set():
        try:
            monitor.capture_snapshot()
        except Exception:
            pass
        for _ in range(10):
            if _stop_event.is_set():
                break
            time.sleep(1)


def start_monitor_thread():
    """Start the background monitor thread if not already running."""
    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        return _monitor_thread
    _stop_event.clear()
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    _monitor_thread.start()
    return _monitor_thread


def stop_monitor_thread():
    """Signal the monitor thread to stop and wait briefly for it."""
    _stop_event.set()
    if _monitor_thread:
        _monitor_thread.join(timeout=0.1)



async def handle_message(message: discord.Message) -> None:
    """Process a Discord message."""
    if message.author.bot:
        return

    content = message.content
    lower = content.lower().strip()
    if lower == "!status":
        monitor.capture_snapshot()
        await message.channel.send(monitor.summarize())
    elif "hello" in lower:
        await message.channel.send("Hey there!")
    else:
        reply = llm.query(content)
        await message.channel.send(reply)

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}.")

@client.event
async def on_message(message: discord.Message):
    await handle_message(message)

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN environment variable not set")

    start_monitor_thread()

    client.run(TOKEN)

