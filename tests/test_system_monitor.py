import unittest
from collections import deque

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


if __name__ == "__main__":
    unittest.main()
