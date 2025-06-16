"""System monitoring utilities for the assistant."""

import sys
import time
from collections import deque
from datetime import datetime
import json
import threading
import os

import importlib
import psutil

try:
    keyboard = importlib.import_module("keyboard")
except ImportError:
    try:
        keyboard = importlib.import_module("keyboard_stub")
    except Exception:
        keyboard = None

try:
    mouse = importlib.import_module("mouse")
except ImportError:
    try:
        mouse = importlib.import_module("mouse_stub")
    except Exception:
        mouse = None

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
    tess_cmd = os.getenv("TESSERACT_CMD")
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
except Exception:  # noqa: E722 - broadly handle any import problem
    pytesseract = None

class SystemMonitor:
    """Tracks active window, inputs, clipboard, screenshots and optional file events."""

    def __init__(self, history_seconds=30, watch_paths=None, screenshot_interval=5, log_path="activity_log.jsonl"):
        self.history_seconds = history_seconds
        self.events = deque()
        self.log_path = log_path

        self.screenshot_interval = screenshot_interval
        self._stop = threading.Event()
        self._screenshot_thread = None

        try:
            self._last_clipboard = pyperclip.paste() if pyperclip else ""
        except Exception:
            self._last_clipboard = ""

        if keyboard:
            keyboard.hook(self._on_keyboard)
        if mouse:
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
        """Return the active window title and application name.

        Falls back to various libraries and platform utilities in order of
        preference. On failure, the title/app will remain "Unknown"."""

        title = "Unknown Window"
        app = "Unknown App"
        pid = None

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

        # On non-Windows systems, attempt native utilities if pywin32 is absent
        if not sys.platform.startswith("win") and title == "Unknown Window":
            try:
                import subprocess
                import re
                if sys.platform.startswith("linux"):
                    active = subprocess.check_output(
                        ["xprop", "-root", "_NET_ACTIVE_WINDOW"], text=True
                    )
                    m = re.search(r"window id # (0x[0-9a-fA-F]+)", active)
                    if m:
                        wid = m.group(1)
                        pid_out = subprocess.check_output(
                            ["xprop", "-id", wid, "_NET_WM_PID"], text=True
                        )
                        pid = int(pid_out.strip().split()[-1])
                        title_out = subprocess.check_output(
                            ["xprop", "-id", wid, "WM_NAME"], text=True
                        )
                        title = title_out.split("=", 1)[-1].strip().strip('"') or title
                        app = psutil.Process(pid).name()
                elif sys.platform == "darwin":
                    script_app = (
                        'tell application "System Events" to get name of first '
                        'process whose frontmost is true'
                    )
                    app = subprocess.check_output(["osascript", "-e", script_app], text=True).strip() or app
                    script_title = (
                        'tell application "System Events" to tell (process 1 whose '
                        'frontmost is true) to get title of front window'
                    )
                    title = subprocess.check_output(["osascript", "-e", script_title], text=True).strip() or title
            except Exception:
                pass

        # If title is still unknown but PID was discovered, fallback to process name
        if title == "Unknown Window" and pid:
            try:
                title = psutil.Process(pid).name()
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

        snapshot = self.to_json()
        self._append_to_log(snapshot)
        return snapshot

    def summarize(self):
        """Return a plain-language summary of recent events."""
        self._prune_history()
        lines = [e[1] for e in self.events]
        summary = "\n".join(lines)
        return f"Recent activity ({datetime.now().strftime('%H:%M:%S')}):\n{summary}"

    def to_json(self):
        """Return a structured summary of recent events."""
        self._prune_history()

        title, app = self._get_active_window_info()

        clipboard = [
            e[1][13:-1]
            for e in self.events
            if e[1].startswith("Copied text:")
        ]
        inputs = [
            e[1]
            for e in self.events
            if e[1].startswith("Pressed key") or e[1].startswith("Mouse")
        ]
        ocr = [
            e[1][12:]
            for e in self.events
            if e[1].startswith("Screen OCR:")
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "active_window": {"title": title, "app": app},
            "clipboard": clipboard,
            "input_events": inputs,
            "ocr_snippets": ocr,
        }

    def _append_to_log(self, data):
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                json.dump(data, f)
                f.write("\n")
        except Exception:
            pass

    def __del__(self):
        self._stop.set()
        if self._screenshot_thread:
            self._screenshot_thread.join(timeout=0.1)
        if self.observer:
            self.observer.stop()
            self.observer.join()


    def capture_screen_text(self):
        """Return OCR text from a screenshot if possible."""
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
                return pytesseract.image_to_string(img).strip()
            except Exception:
                return ""
        return ""

    def save_screen_memo(self, label=None, directory="ai_memos", allow_empty=False):
        """Capture screen text and save to a memo file.

        Parameters
        ----------
        label : str, optional
            Optional label for the memo filename.
        directory : str, default "ai_memos"
            Directory where the memo will be created.
        allow_empty : bool, default False
            When True, a memo file is created even if no text is captured.
        """
        text = self.capture_screen_text()
        if not text and allow_empty:
            text = "No screen text captured"
        if text:
            from memo_utils import save_memo
            save_memo(text, label, directory)
            return True
        return False

    def scan_processes(self):
        """Return a list of suspicious processes using simple heuristics."""
        keywords = ["hack", "malware", "virus", "keylog", "spy", "trojan"]
        suspicious = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                info = proc.info
                name = (info.get("name") or "").lower()
                exe = (info.get("exe") or "").lower()
                if any(k in name or k in exe for k in keywords):
                    suspicious.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                continue
        return suspicious
