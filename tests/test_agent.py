from collections import deque

from agent import ClippyAgent
from system_monitor import SystemMonitor


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
    agent = ClippyAgent(window)
    agent.monitor = _make_monitor(tmp_path)

    class DummyLLM:
        def query(self, prompt):
            return "ok"
    agent.llm = DummyLLM()

    agent.handle_text("please memo this")

    files = list(tmp_path.iterdir())
    assert files
    assert any("dummy text" in f.read_text() for f in files)
