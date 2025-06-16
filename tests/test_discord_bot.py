import asyncio
from types import SimpleNamespace

import discord_bot

class DummyChannel:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)

class DummyAuthor:
    def __init__(self, bot=False):
        self.bot = bot


def test_handle_message_hello():
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="hello there", channel=channel)
    asyncio.run(discord_bot.handle_message(message))
    assert channel.sent == ["Hey there!"]


def test_handle_message_llm(monkeypatch):
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="question", channel=channel)

    class DummyLLM:
        def __init__(self):
            self.prompt = None
        def query(self, prompt):
            self.prompt = prompt
            return "reply"

    dummy = DummyLLM()
    monkeypatch.setattr(discord_bot, "llm", dummy)
    asyncio.run(discord_bot.handle_message(message))
    assert dummy.prompt == "question"
    assert channel.sent == ["reply"]


def test_handle_message_status(monkeypatch):
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="!status", channel=channel)

    dummy_monitor = SimpleNamespace(summarize=lambda: "summary", capture_snapshot=lambda: None)
    monkeypatch.setattr(discord_bot, "monitor", dummy_monitor)
    asyncio.run(discord_bot.handle_message(message))
    assert channel.sent == ["summary"]


def test_monitor_thread_start_stop():
    t = discord_bot.start_monitor_thread()
    assert t.is_alive()
    discord_bot.stop_monitor_thread()

