# Discord Bot for AI Assistant Project
# Application ID: 311019517365190656
# Public Key: acf2dda637df5e9d50726ab5c4b886eb9e9b616927ba209afbaf54b449b067be

import os
import threading
import time
import asyncio
import re
import logging

import discord
from system_monitor import SystemMonitor
import discord_agent
import system_controller
import gmail_utils

TOKEN = os.getenv("DISCORD_TOKEN")
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True  # allow reading message text
client = discord.Client(intents=intents)
monitor = SystemMonitor()
_agents = {}

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
    logging.info("Command received: %s", content)
    lower = content.lower().strip()
    if (
        lower == "!status"
        or "screen status" in lower
        or re.search(r"what[’']?s on (?:the |my )?screen", lower)
        or re.search(r"what[’']?s on (?:the |my )?desktop", lower)
    ):
        monitor.capture_snapshot()
        await message.channel.send(monitor.summarize())
        return

    m = re.match(r"\s*(?:please|could you|can you|would you)?\s*open\s+(.+)", content, re.I)
    if m:
        path = m.group(1).strip()
        logging.info("Calling open_file(%s)", path)
        success = system_controller.open_file(path)
        logging.info("open_file returned %s", success)
        await message.channel.send("Opened." if success else "Failed to open.")
        return

    m = re.match(r"\s*(?:please|could you|can you|would you)?\s*start\s+(.+)", content, re.I)
    if m:
        cmd = m.group(1).strip()
        logging.info("Calling start_process(%s)", cmd)
        proc = system_controller.start_process(cmd)
        logging.info("start_process returned %s", bool(proc))
        await message.channel.send(
            "Process started." if proc else "Failed to start process."
        )
        return

    if lower.strip() == "close":
        logging.info("Calling close_active_window()")
        success = system_controller.close_active_window()
        logging.info("close_active_window returned %s", success)
        await message.channel.send(
            "Closed active window." if success else "Failed to close window."
        )
        return

    m = re.match(r"\s*(?:please|could you|can you|would you)?\s*close\s+(.+)", content, re.I)
    if m:
        name = m.group(1).strip()
        logging.info("Calling close_window_by_name(%s)", name)
        success = system_controller.close_window_by_name(name)
        logging.info("close_window_by_name returned %s", success)
        await message.channel.send(
            f"Closed {name}." if success else f"Failed to close {name}."
        )
        return

    m = re.match(r"!gmail\s+(.+)", content, re.I)
    if m:
        query = m.group(1).strip()
        try:
            service = gmail_utils.get_service()
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None, gmail_utils.search_messages, service, query
            )
        except Exception as exc:
            logging.exception("Error searching Gmail")
            await message.channel.send(f"Error searching Gmail: {exc}")
            return
        if results:
            lines = "\n".join(f"- {sub}" for _, sub in results)
            await message.channel.send(f"Found {len(results)} messages:\n{lines}")
        else:
            await message.channel.send("No messages found.")
        return

    loop = asyncio.get_running_loop()
    agent = _agents.get(message.channel.id)
    if agent is None:
        agent = discord_agent.DiscordAgent(message.channel, loop)
        agent.start()
        _agents[message.channel.id] = agent

    await asyncio.get_running_loop().run_in_executor(None, agent.handle_text, content)

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

