import os
import sys
import subprocess

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    from pywinauto import Application
except Exception:
    Application = None


def open_file(path):
    """Open a file or folder with the default application."""
    if sys.platform.startswith("win"):
        try:
            os.startfile(path)  # type: ignore[attr-defined]
            return True
        except Exception:
            return False
    cmd = ["open", path] if sys.platform == "darwin" else ["xdg-open", path]
    try:
        subprocess.Popen(cmd)
        return True
    except Exception:
        return False


def close_active_window():
    """Close the currently active window if possible."""
    if pyautogui:
        try:
            pyautogui.hotkey("alt", "f4")
            return True
        except Exception:
            pass
    if Application:
        try:
            app = Application().connect(active_only=True)
            app.top_window().close()
            return True
        except Exception:
            pass
    return False


def close_window_by_name(name: str) -> bool:
    """Close a window matching ``name`` using pywinauto when available."""
    if Application:
        try:
            app = Application().connect(title_re=name)
            app.top_window().close()
            return True
        except Exception:
            pass
    return False


def start_process(cmd):
    """Start a new process using subprocess."""
    try:
        return subprocess.Popen(cmd, shell=isinstance(cmd, str))
    except Exception:
        return None
