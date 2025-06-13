# ai_assistant
This repository contains a simple desktop assistant using PyQt5.

The `SystemMonitor` component now tracks:

- Active window title and application name (using `pygetwindow`, `pywin32`, or `pywinauto` when available).
  When these fail, it now tries platform commands (`xprop`/`wmctrl` on Linux or
  `osascript` on macOS) and finally falls back to the process name if a PID is
  known.
- Text elements inside the focused window on Windows.
- Clipboard changes in real time.
- Keyboard and mouse activity.
- Optional file modifications using `watchdog`.

If the window information libraries are unavailable, the monitor falls back to `"Unknown Window"`.

Legacy test utilities like `test_script.py` and the separate `key_logger.py` have been removed.
