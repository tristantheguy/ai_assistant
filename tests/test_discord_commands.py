import asyncio
from types import SimpleNamespace

import discord_bot


class DummyChannel:
    def __init__(self):
        self.sent = []
        self.id = 1

    async def send(self, msg):
        self.sent.append(msg)


class DummyAuthor:
    def __init__(self, bot=False):
        self.bot = bot


def _reset_agents():
    discord_bot._agents.clear()


async def _run_message(content, monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content=content, channel=channel)
    return channel, message


async def _assert_system_command(monkeypatch, content, attr, arg):
    channel, message = await _run_message(content, monkeypatch)

    calls = {}
    monkeypatch.setattr(discord_bot.system_controller, attr, lambda x: calls.setdefault("arg", x))

    class DummyDA:
        def __init__(self, *a, **k):
            raise AssertionError("DiscordAgent should not be started")

    monkeypatch.setattr(discord_bot.discord_agent, "DiscordAgent", DummyDA)

    await discord_bot.handle_message(message)

    assert calls.get("arg") == arg
    assert not discord_bot._agents


def test_open_start_close_commands(monkeypatch):
    asyncio.run(_assert_system_command(monkeypatch, "open file.txt", "open_file", "file.txt"))
    asyncio.run(_assert_system_command(monkeypatch, "start echo hi", "start_process", "echo hi"))
    asyncio.run(_assert_system_command(monkeypatch, "close chrome", "close_window_by_name", "chrome"))
