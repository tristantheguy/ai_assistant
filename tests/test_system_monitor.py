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
            self.assertIsNotNone(sm.keyboard)
            self.assertIsNotNone(sm.mouse)
            self.assertTrue(hasattr(sm.keyboard, "hook"))
            self.assertTrue(hasattr(sm.mouse, "hook"))
    def test_import_without_tesseract_cmd(self):
        import importlib
        import system_monitor as sm
        import os
        os.environ.pop("TESSERACT_CMD", None)
        importlib.reload(sm)
        monitor = sm.SystemMonitor.__new__(sm.SystemMonitor)
        import threading
        monitor._stop = threading.Event()
        monitor._screenshot_thread = None
        self.assertTrue(hasattr(sm, "pytesseract"))
        monitor.observer = None
        self.assertIsNotNone(monitor)
        importlib.reload(sm)

    def test_summarize_high_level(self):
        monitor = self._make_monitor()

        import time
        now = time.time()
        monitor.events.append((now, "Pressed key: a"))
        monitor.events.append((now, "Pressed key: b"))
        monitor.events.append((now, "Mouse move"))
        monitor.events.append((now, "Copied text: 'hello'"))

        monitor._get_active_window_info = lambda: ("File.txt - Notepad", "notepad.exe")
        monitor._check_clipboard = lambda: None

        class P:
            def __init__(self, name):
                self.info = {"name": name}

        def fake_iter(attrs=None):
            return [P("notepad.exe"), P("chrome.exe"), P("System"), P(""), P("calc.exe")]

        import psutil

        original_iter = psutil.process_iter
        psutil.process_iter = fake_iter
        try:
            summary = monitor.summarize()
        finally:
            psutil.process_iter = original_iter

        self.assertIn("File.txt - Notepad", summary)
        self.assertIn("2 keys pressed", summary)
        self.assertIn("1 mouse move", summary)
        self.assertIn("hello", summary)
        self.assertIn("chrome.exe", summary)
        self.assertIn("1 other", summary)

    def test_capture_snapshot_filters_and_sorts_processes(self):
        monitor = self._make_monitor()
        monitor._get_active_window_info = lambda: ("Win", "app.exe")
        monitor._extract_ui_text = lambda: []
        monitor._check_clipboard = lambda: None
        monitor._append_to_log = lambda data: None

        import psutil

        class P:
            def __init__(self, name, cpu=0, mem=0):
                self.info = {"name": name}
                self._cpu = cpu
                self._mem = mem

            def cpu_percent(self, interval=None):
                return self._cpu

            class Mem:
                def __init__(self, rss):
                    self.rss = rss

            def memory_info(self):
                return self.Mem(self._mem)

        def fake_iter(attrs=None):
            return [
                P("System"),
                P("Registry"),
                P(""),
                P("chrome.exe", cpu=10, mem=200),
                P("notes.exe", cpu=20, mem=100),
            ]

        original_iter = psutil.process_iter
        psutil.process_iter = fake_iter
        try:
            monitor.capture_snapshot(sort_by="cpu")
        finally:
            psutil.process_iter = original_iter

        run_event = [e[1] for e in monitor.events if e[1].startswith("Running apps")][0]
        names_list = eval(run_event[len("Running apps: "):])
        self.assertEqual(names_list, ["notes.exe", "chrome.exe"])


if __name__ == "__main__":
    unittest.main()
