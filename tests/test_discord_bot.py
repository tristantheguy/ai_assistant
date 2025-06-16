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


def test_handle_message_status_synonyms(monkeypatch):
    _reset_agents()
    dummy_monitor = SimpleNamespace(summarize=lambda: "summary", capture_snapshot=lambda: None)
    monkeypatch.setattr(discord_bot, "monitor", dummy_monitor)
    for text in [
        "what's on the screen?",
        "please show screen status",
        "what's on my desktop",
        "what's on the desktop",
    ]:
        channel = DummyChannel()
        message = SimpleNamespace(author=DummyAuthor(), content=text, channel=channel)
        asyncio.run(discord_bot.handle_message(message))
        assert channel.sent == ["summary"]


def test_monitor_thread_start_stop():
    t = discord_bot.start_monitor_thread()
    assert t.is_alive()
    discord_bot.stop_monitor_thread()


def test_handle_message_open_command(monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="please open foo.txt", channel=channel)

    calls = {}
    monkeypatch.setattr(discord_bot.system_controller, 'open_file', lambda p: calls.setdefault('path', p))

    asyncio.run(discord_bot.handle_message(message))

    assert calls['path'] == 'foo.txt'
    assert channel.sent == ["Opened."]
    assert not discord_bot._agents


def test_handle_message_start_command(monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="could you start echo hi", channel=channel)

    calls = {}
    monkeypatch.setattr(discord_bot.system_controller, 'start_process', lambda c: calls.setdefault('cmd', c))

    asyncio.run(discord_bot.handle_message(message))

    assert calls['cmd'] == 'echo hi'
    assert channel.sent == ["Process started."]
    assert not discord_bot._agents


def test_handle_message_close_command(monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="please close calc", channel=channel)

    calls = {}
    monkeypatch.setattr(discord_bot.system_controller, 'close_window_by_name', lambda n: calls.setdefault('name', n))

    asyncio.run(discord_bot.handle_message(message))

    assert calls['name'] == 'calc'
    assert channel.sent == ["Closed calc."]
    assert not discord_bot._agents


def test_handle_message_close_active_window(monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="close", channel=channel)

    calls = {}
    monkeypatch.setattr(discord_bot.system_controller, 'close_active_window', lambda: calls.setdefault('called', True))

    asyncio.run(discord_bot.handle_message(message))

    assert calls.get('called')
    assert channel.sent == ["Closed active window."]
    assert not discord_bot._agents


def test_handle_message_ignore_open_in_sentence(monkeypatch):
    _reset_agents()
    channel = DummyChannel()
    message = SimpleNamespace(author=DummyAuthor(), content="I am open to suggestions", channel=channel)

    calls = {}
    monkeypatch.setattr(discord_bot.system_controller, 'open_file', lambda p: calls.setdefault('path', p))

    class DummyClippy:
        def __init__(self, window, *a, **kw):
            self.window = window
            self.monitor = SimpleNamespace(save_screen_memo=lambda **k: None)

        def start(self):
            pass

        def handle_text(self, text):
            self.window.display_message("reply")

    monkeypatch.setattr(discord_bot.discord_agent, "ClippyAgent", DummyClippy)

    asyncio.run(discord_bot.handle_message(message))

    assert 'path' not in calls
    assert channel.sent == ["reply"]
