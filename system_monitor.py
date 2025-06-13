"""System monitoring utilities for the assistant."""

import sys
import time
from collections import deque
from datetime import datetime

import psutil
import keyboard
import mouse

try:
    import pygetwindow as gw
except Exception:  # noqa: E722 - broadly handle any import problem
    gw = None

try:
    from pywinauto import desktop
    from pywinauto.application import Application
except Exception:  # noqa: E722 - broadly handle any import problem
    desktop = None
    Application = None

try:
    import pyperclip
except Exception:  # noqa: E722 - broadly handle any import problem
    pyperclip = None

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except Exception:  # noqa: E722 - broadly handle any import problem
    FileSystemEventHandler = None
    Observer = None

class SystemMonitor:
    """Tracks active window, inputs, clipboard and optional file events."""

    def __init__(self, history_seconds=30, watch_paths=None):
        self.history_seconds = history_seconds
        self.events = deque()

        self._last_clipboard = pyperclip.paste() if pyperclip else ""

        keyboard.hook(self._on_keyboard)
        mouse.hook(self._on_mouse)

        self.observer = None
        if watch_paths and Observer:
            self.observer = Observer()

            class _Handler(FileSystemEventHandler):
                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer

                def on_modified(self, event):
                    if not event.is_directory:
                        self.outer._record(
                            f"Modified file: {event.src_path}"
                        )

                def on_created(self, event):
                    if not event.is_directory:
                        self.outer._record(
                            f"Created file: {event.src_path}"
                        )

            handler = _Handler(self)
            for path in watch_paths:
                self.observer.schedule(handler, path, recursive=True)
            self.observer.start()

    def _record(self, message):
        """Add a timestamped event message."""
        self.events.append((time.time(), message))

    def _on_keyboard(self, event):
        self._record(f"Pressed key: {event.name}")

    def _on_mouse(self, event):
        self._record(f"Mouse {event.event_type}")

    def _prune_history(self):
        cutoff = time.time() - self.history_seconds
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def _check_clipboard(self):
        if not pyperclip:
            return
        try:
            current = pyperclip.paste()
        except Exception:
            return
        if current != self._last_clipboard:
            self._last_clipboard = current
            self._record(f"Copied text: '{current}'")

    def _get_active_window_info(self):
        title = "Unknown Window"
        app = "Unknown App"
        if gw:
            try:
                win = gw.getActiveWindow()
                if win:
                    title = win.title or title
            except Exception:
                pass
        if sys.platform.startswith("win") and desktop:
            try:
                win = desktop.active_window()
                if win:
                    title = win.window_text() or title
                    if hasattr(win, "process_id"):
                        pid = win.process_id()
                        try:
                            app = psutil.Process(pid).name()
                        except Exception:
                            pass
            except Exception:
                pass
        return title, app

    def _extract_ui_text(self):
        texts = []
        if sys.platform.startswith("win") and desktop:
            try:
                win = desktop.active_window()
                if win:
                    for ctrl in win.descendants():
                        txt = ctrl.window_text()
                        if txt:
                            texts.append(txt)
            except Exception:
                pass
        return texts

    def capture_snapshot(self):
        """Gather system context and record meaningful events."""
        self._prune_history()
        self._check_clipboard()

        title, app = self._get_active_window_info()
        ui_texts = self._extract_ui_text()

        self._record(f"Active window: {title} ({app})")
        if ui_texts:
            snippet = ", ".join(ui_texts[:5])
            self._record(f"Visible elements: {snippet}")

        processes = {p.pid: p.name() for p in psutil.process_iter(["name"])}
        self._record(f"Running apps: {list(processes.values())[:5]}")

    def summarize(self):
        """Return a plain-language summary of recent events."""
        self._prune_history()
        lines = [e[1] for e in self.events]
        summary = "\n".join(lines)
        return f"Recent activity ({datetime.now().strftime('%H:%M:%S')}):\n{summary}"

    def __del__(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
