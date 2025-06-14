import os
import discord
from llm_client import OllamaClient


class DiscordBot(discord.Client):
    """Simple Discord bot that forwards messages to an LLM."""

    def __init__(self, llm=None, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, **kwargs)
        self.llm = llm or OllamaClient()

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def on_message(self, message):
        if message.author.bot:
            return
        reply = self.llm.query(message.content)
        await message.channel.send(reply)


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN environment variable not set")
    bot = DiscordBot()
    bot.run(token)


if __name__ == "__main__":
    main()
