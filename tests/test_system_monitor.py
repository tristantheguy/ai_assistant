import unittest
from collections import deque
from pathlib import Path

from system_monitor import SystemMonitor


class DummyWheelEvent:
    def __init__(self, delta=1):
        self.event_type = "wheel"
        self.delta = delta


class DummyMoveEvent:
    def __init__(self):
        self.event_type = "move"


class SystemMonitorTest(unittest.TestCase):
    def _make_monitor(self):
        monitor = SystemMonitor.__new__(SystemMonitor)
        monitor.events = deque()
        monitor.history_seconds = 30
        import threading
        monitor._stop = threading.Event()
        monitor._screenshot_thread = None
        monitor.observer = None
        return monitor

    def test_wheel_event_no_exception(self):
        monitor = self._make_monitor()
        event = DummyWheelEvent(delta=5)
        monitor._on_mouse(event)
        self.assertTrue(monitor.events)
        self.assertIn("wheel", monitor.events[-1][1])
        self.assertIn("delta=5", monitor.events[-1][1])

    def test_move_event_no_exception(self):
        monitor = self._make_monitor()
        event = DummyMoveEvent()
        monitor._on_mouse(event)
        self.assertTrue(monitor.events)
        self.assertIn("move", monitor.events[-1][1])

    def test_save_screen_memo_allow_empty_creates_file(self):
        import tempfile
        monitor = self._make_monitor()
        monitor.capture_screen_text = lambda: ""
        with tempfile.TemporaryDirectory() as tmpdir:
            success = monitor.save_screen_memo(directory=tmpdir, allow_empty=True)
            self.assertTrue(success)
            files = list(Path(tmpdir).iterdir())
            self.assertTrue(files)
            text = files[0].read_text()
            self.assertIn("No screen text captured", text)

    def test_scan_processes_monkeypatch(self):
        monitor = self._make_monitor()

        class P:
            def __init__(self, pid, name, exe):
                self.info = {"pid": pid, "name": name, "exe": exe}

        def fake_iter(attrs):
            return [
                P(1, "good.exe", "/bin/good.exe"),
                P(2, "bad-virus.exe", "/tmp/bad-virus.exe"),
            ]

        import psutil

        original_iter = psutil.process_iter
        psutil.process_iter = fake_iter
        try:
            suspicious = monitor.scan_processes()
        finally:
            psutil.process_iter = original_iter

        names = [p["name"] for p in suspicious]
        self.assertIn("bad-virus.exe", names)

    def test_init_without_input_modules(self):
        import importlib
        import builtins
        import system_monitor as sm

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in ("keyboard", "mouse"):
                raise ImportError()
            return real_import(name, globals, locals, fromlist, level)

        with unittest.mock.patch("builtins.__import__", side_effect=fake_import):
            importlib.reload(sm)
            monitor = sm.SystemMonitor()
            self.assertIsNone(sm.keyboard)
            self.assertIsNone(sm.mouse)
        importlib.reload(sm)


    def test_init_without_tesseract_env(self):
        import importlib
        import os
        import system_monitor as sm

        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TESSERACT_CMD", None)
            importlib.reload(sm)
            monitor = sm.SystemMonitor()
            self.assertIsNotNone(monitor)
        importlib.reload(sm)


if __name__ == "__main__":
    unittest.main()
