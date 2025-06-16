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


def test_handle_message_reply(monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="hi", channel=channel)

    class DummyClippy:
        def __init__(self, window, *a, **kw):
            self.window = window
            self.received = None
            self.monitor = SimpleNamespace(save_screen_memo=lambda **k: None)

        def start(self):
            pass

        def handle_text(self, text):
            self.received = text
            self.window.display_message("reply")

    monkeypatch.setattr(discord_bot.discord_agent, "ClippyAgent", DummyClippy)

    asyncio.run(discord_bot.handle_message(message))
    assert channel.sent == ["reply"]


def test_handle_message_triggers_memo(monkeypatch, tmp_path):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="please memo", channel=channel)

    calls = {}

    class DummyClippy:
        def __init__(self, window, *a, **kw):
            self.window = window
            self.monitor = SimpleNamespace(save_screen_memo=lambda **k: calls.setdefault("memo", 0) or calls.update(memo=calls.get("memo",0)+1))

        def start(self):
            pass

        def handle_text(self, text):
            self.window.display_message("ok")
            if "memo" in text.lower():
                self.monitor.save_screen_memo(label=text, allow_empty=True)

    monkeypatch.setattr(discord_bot.discord_agent, "ClippyAgent", DummyClippy)

    asyncio.run(discord_bot.handle_message(message))
    assert channel.sent == ["ok"]
    assert calls.get("memo") == 1


def test_handle_message_status(monkeypatch):
    _reset_agents()
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
