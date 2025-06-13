# ai_assistant
This repository contains a simple desktop assistant using PyQt5.

The `SystemMonitor` component now tracks:

- Active window title and application name (using `pygetwindow` or `pywinauto` when available).
- Text elements inside the focused window on Windows.
- Clipboard changes in real time.
- Keyboard and mouse activity.
- Optional file modifications using `watchdog`.

If the window information libraries are unavailable, the monitor falls back to `"Unknown Window"`.
