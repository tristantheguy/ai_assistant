import unittest
from collections import deque
from unittest import mock

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

    def test_env_var_sets_tesseract_path(self):
        import importlib
        import sys
        import types
        import os

        dummy = types.SimpleNamespace(pytesseract=types.SimpleNamespace())
        with mock.patch.dict(sys.modules, {"pytesseract": dummy}):
            with mock.patch.dict(os.environ, {"TESSERACT_CMD": "/opt/custom"}):
                mod = importlib.reload(importlib.import_module("system_monitor"))
                self.assertEqual(
                    dummy.pytesseract.tesseract_cmd, "/opt/custom"
                )
        importlib.reload(mod)


if __name__ == "__main__":
    unittest.main()
