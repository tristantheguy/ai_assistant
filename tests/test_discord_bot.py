import asyncio
from types import SimpleNamespace

from discord_bot import DiscordBot


class DummyAuthor:
    def __init__(self, is_bot=False):
        self.bot = is_bot


class DummyChannel:
    def __init__(self):
        self.sent = None

    async def send(self, message):
        self.sent = message


class DummyMessage:
    def __init__(self, content, author_bot=False):
        self.content = content
        self.author = DummyAuthor(author_bot)
        self.channel = DummyChannel()


def test_user_message_replies():
    llm = SimpleNamespace(query=lambda text: text.upper())
    bot = DiscordBot(llm=llm)
    msg = DummyMessage("hello")
    asyncio.run(bot.on_message(msg))
    assert msg.channel.sent == "HELLO"


def test_bot_message_ignored():
    llm = SimpleNamespace(query=lambda text: "bad")
    bot = DiscordBot(llm=llm)
    msg = DummyMessage("ignored", author_bot=True)
    asyncio.run(bot.on_message(msg))
    assert msg.channel.sent is None
