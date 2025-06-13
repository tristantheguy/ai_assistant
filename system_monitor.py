import time
import psutil
try:
    import pygetwindow as gw
except Exception:  # noqa: E722 - broadly handle any import problem
    gw = None
import keyboard
import mouse
from collections import deque
from datetime import datetime

class SystemMonitor:
    """Tracks processes, foreground window and basic input."""

    def __init__(self, history_seconds=30):
        self.history_seconds = history_seconds
        self.events = deque()

        keyboard.hook(self._on_keyboard)
        mouse.hook(self._on_mouse)

    def _on_keyboard(self, event):
        self.events.append((time.time(), f"Keyboard: {event.name}"))

    def _on_mouse(self, event):
        self.events.append((time.time(), f"Mouse: {event.event_type}"))

    def _prune_history(self):
        cutoff = time.time() - self.history_seconds
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def capture_snapshot(self):
        self._prune_history()
        timestamp = time.time()
        try:
            if gw:
                fg_window = gw.getActiveWindow().title
            else:
                fg_window = "Unknown Window"
        except Exception:
            fg_window = "Unknown Window"
        processes = {p.pid: p.name() for p in psutil.process_iter(["name"])}
        self.events.append((timestamp, f"Foreground window: {fg_window}"))
        self.events.append((timestamp, f"Processes: {list(processes.values())[:5]}"))

    def summarize(self):
        self._prune_history()
        lines = [e[1] for e in self.events]
        summary = " | ".join(lines)
        return f"Recent activity ({datetime.now().strftime('%H:%M:%S')}): {summary}"
