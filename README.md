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

Snapshots are written to `activity_log.jsonl` in the repository root.

If the window information libraries are unavailable, the monitor falls back to `"Unknown Window"`.

Legacy test utilities like `test_script.py` and the separate `key_logger.py` have been removed.

## Error reporting

Running `main.py` is now wrapped with an `ErrorReporter`. When an
exception is raised, the full traceback is sent to a local Ollama
instance and the model explains the problem. The traceback and LLM
response are appended to `error_report.txt` so you can review past
failures.

## Interactive commands

The assistant window now includes a small text box. Type a prompt and press
Enter to send it directly to the LLM. The reply appears in the floating window
so you can interact with the assistant in real time without using your
microphone.
