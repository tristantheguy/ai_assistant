"""System monitoring utilities for the assistant."""

import sys
import time
from collections import deque
from datetime import datetime
import threading

import psutil
import keyboard
import mouse

try:
    import win32gui
    import win32process
except Exception:  # noqa: E722 - broadly handle any import problem
    win32gui = None
    win32process = None

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

try:
    from PIL import ImageGrab
except Exception:  # noqa: E722 - broadly handle any import problem
    ImageGrab = None

try:
    import pyautogui
except Exception:  # noqa: E722 - broadly handle any import problem
    pyautogui = None

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
except Exception:  # noqa: E722 - broadly handle any import problem
    pytesseract = None

class SystemMonitor:
    """Tracks active window, inputs, clipboard, screenshots and optional file events."""

    def __init__(self, history_seconds=30, watch_paths=None, screenshot_interval=5):
        self.history_seconds = history_seconds
        self.events = deque()

        self.screenshot_interval = screenshot_interval
        self._stop = threading.Event()
        self._screenshot_thread = None

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

        if pytesseract and (ImageGrab or pyautogui):
            self._screenshot_thread = threading.Thread(
                target=self._screenshot_loop, daemon=True
            )
            self._screenshot_thread.start()

    def _record(self, message):
        """Add a timestamped event message."""
        self.events.append((time.time(), message))

    def _on_keyboard(self, event):
        self._record(f"Pressed key: {event.name}")

    def _on_mouse(self, event):
        event_type = getattr(event, "event_type", None) or event.__class__.__name__
        message = f"Mouse {event_type}"
        if hasattr(event, "delta"):
            message += f" delta={event.delta}"
        self._record(message)

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
        if sys.platform.startswith("win") and win32gui:
            try:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    title = win32gui.GetWindowText(hwnd) or title
                    if win32process:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            app = psutil.Process(pid).name()
                        except Exception:
                            pass
            except Exception:
                pass
        if sys.platform.startswith("win") and desktop and app == "Unknown App":
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

    def _capture_screen(self):
        img = None
        if ImageGrab:
            try:
                img = ImageGrab.grab()
            except Exception:
                img = None
        if img is None and pyautogui:
            try:
                img = pyautogui.screenshot()
            except Exception:
                img = None

        if img and pytesseract:
            try:
                text = pytesseract.image_to_string(img)
            except Exception:
                text = ""
            if text.strip():
                snippet = text.strip().replace("\n", " ")[:200]
                self._record(f"Screen OCR: {snippet}")

    def _screenshot_loop(self):
        while not self._stop.is_set():
            self._capture_screen()
            for _ in range(self.screenshot_interval):
                if self._stop.is_set():
                    break
                time.sleep(1)

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
        self._stop.set()
        if self._screenshot_thread:
            self._screenshot_thread.join(timeout=0.1)
        if self.observer:
            self.observer.stop()
            self.observer.join()
