from collections import deque

from agent import ClippyAgent
from system_monitor import SystemMonitor
import time
import json


class DummyWindow:
    def __init__(self):
        self.last = None

    def display_message(self, msg):
        self.last = msg


def _make_monitor(tmp_path):
    monitor = SystemMonitor.__new__(SystemMonitor)
    monitor.events = deque()
    monitor.history_seconds = 30
    monitor.log_path = tmp_path / "log.txt"
    import threading
    monitor._stop = threading.Event()
    monitor._screenshot_thread = None
    monitor.observer = None
    monitor.capture_snapshot = lambda: {}
    monitor.capture_screen_text = lambda: "dummy text"

    def save_screen_memo(label=None, directory="ai_memos", allow_empty=False):
        return SystemMonitor.save_screen_memo(
            monitor, label, directory=tmp_path, allow_empty=allow_empty
        )

    monitor.save_screen_memo = save_screen_memo
    return monitor


def test_handle_text_triggers_memo(tmp_path):
    window = DummyWindow()
    agent = ClippyAgent(window, notify_interval=None)
    agent.monitor = _make_monitor(tmp_path)

    class DummyLLM:
        def query(self, prompt):
            return "ok"
    agent.llm = DummyLLM()

    agent.handle_text("please memo this")

    files = list(tmp_path.iterdir())
    assert files
    assert any("dummy text" in f.read_text() for f in files)


def test_loop_continues_on_error(tmp_path):
    window = DummyWindow()
    agent = ClippyAgent(window, poll_interval=0, notify_interval=None)
    agent.monitor = _make_monitor(tmp_path)

    class FailingLLM:
        def __init__(self):
            self.calls = 0

        def add_context(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("fail")

    agent.llm = FailingLLM()

    agent.start()
    time.sleep(0.05)
    assert agent.thread.is_alive()
    time.sleep(0.05)
    # add_context should be retried after failure
    assert agent.llm.calls >= 2
    assert window.last is None
    agent.stop()


def test_loop_continues_with_reporter(tmp_path):
    window = DummyWindow()

    class DummyReporter:
        def __init__(self):
            self.count = 0

        def handle_exception(self):
            self.count += 1

    reporter = DummyReporter()
    agent = ClippyAgent(window, poll_interval=0, error_reporter=reporter, notify_interval=None)
    agent.monitor = _make_monitor(tmp_path)

    class FailingLLM:
        def __init__(self):
            self.calls = 0

        def add_context(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("fail")

    agent.llm = FailingLLM()

    agent.start()
    time.sleep(0.05)
    assert agent.thread.is_alive()
    time.sleep(0.05)
    assert reporter.count == 1
    # No LLM output shown automatically
    assert window.last is None
    agent.stop()


def test_no_query_on_unchanged_snapshot(tmp_path):
    window = DummyWindow()
    agent = ClippyAgent(window, poll_interval=0, notify_interval=1000)
    agent.monitor = _make_monitor(tmp_path)

    class DummyLLM:
        def __init__(self):
            self.calls = 0

        def add_context(self, prompt):
            self.calls += 1

    agent.llm = DummyLLM()

    agent.start()
    time.sleep(0.05)
    first_calls = agent.llm.calls
    time.sleep(0.05)
    agent.stop()

    assert first_calls == agent.llm.calls == 1


def test_handle_text_summary(tmp_path):
    window = DummyWindow()
    agent = ClippyAgent(window, notify_interval=None)
    agent.monitor = _make_monitor(tmp_path)

    snapshot = {"foo": "bar"}
    agent.monitor.capture_snapshot = lambda: snapshot
    agent._last_snapshot = snapshot

    class DummyLLM:
        def __init__(self):
            self.prompt = None

        def query(self, prompt):
            self.prompt = prompt
            return "ok"

    agent.llm = DummyLLM()

    agent.handle_text("summary")

    assert agent.llm.prompt == json.dumps(snapshot)
    assert window.last == "ok"
