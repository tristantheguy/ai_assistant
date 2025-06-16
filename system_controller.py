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

try:
    import psutil
except Exception:
    psutil = None


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


def close_window_by_name(app_name: str) -> bool:
    """Close a window or process matching ``app_name``.

    Uses ``pywinauto`` to close the first window whose title matches
    ``app_name`` when available. If that fails, ``psutil`` is used to
    terminate a process whose name contains ``app_name``.
    """
    if Application:
        try:
            app = Application().connect(title_re=app_name)
            app.top_window().close()
            return True
        except Exception:
            pass

    if psutil:
        terminated = False
        for proc in psutil.process_iter(["name"]):
            try:
                if app_name.lower() in (proc.info.get("name") or "").lower():
                    proc.terminate()
                    terminated = True
            except Exception:
                continue
        if terminated:
            return True

    return False


def start_process(cmd):
    """Start a new process using subprocess."""
    try:
        return subprocess.Popen(cmd, shell=isinstance(cmd, str))
    except Exception:
        return None
