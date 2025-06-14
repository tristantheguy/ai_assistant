# Discord Bot for AI Assistant Project
# Application ID: 311019517365190656
# Public Key: acf2dda637df5e9d50726ab5c4b886eb9e9b616927ba209afbaf54b449b067be

import os
import discord
from llm_client import OllamaClient

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # allow reading message text
client = discord.Client(intents=intents)
llm = OllamaClient()

async def handle_message(message: discord.Message) -> None:
    """Process a Discord message."""
    if message.author.bot:
        return

    content = message.content
    if "hello" in content.lower():
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
    client.run(TOKEN)

