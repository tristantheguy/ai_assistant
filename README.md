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
Enter to send it directly to the LLM. Replies accumulate in the floating window
so you have a scrollable running log of the conversation. The window can now be
resized like a normal application.

### Custom system prompt

`OllamaClient` now accepts a `system_prompt` argument. This optional string
sets the initial system message used for every conversation. If omitted, the
client defaults to "You are a helpful assistant." Passing a different value lets
you customize the assistant's personality.

## Memos and process scans

Use `SystemMonitor.save_screen_memo()` to capture on-screen text and save it in the `ai_memos` folder. The helper `memo_utils.save_memo()` writes a timestamped file with a descriptive name. Typing **memo**, **remember**, or **note** in the assistant's text box automatically triggers this capture. Pass `allow_empty=True` to `save_screen_memo` to force a memo even when OCR text can't be captured (e.g. if dependencies are missing).

`SystemMonitor.scan_processes()` performs a simple heuristic check for suspicious processes based on keywords like "malware" or "virus".
