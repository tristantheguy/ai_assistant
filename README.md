# ai_assistant
This repository contains a simple desktop assistant using PyQt5.

## Installation

Use pip to install the required packages **before running any of the scripts or tests**:

```bash
pip install -r requirements.txt
```

Run the test suite with:

```bash
pytest
```

You can optionally set the `TESSERACT_CMD` environment variable if Tesseract OCR is installed in a non-standard location.

The GUI file browser defaults to `Path.home() / "Documents" / "AI Assistant"`. Set the `AI_ASSISTANT_FOLDER` environment variable or pass `folder_path` to `CodeAssistantGUI` to use a different directory.

The `SystemMonitor` component now tracks:

- Active window title and application name (using `pygetwindow`, `pywin32`, or `pywinauto` when available).
  When these fail, it now tries platform commands (`xprop`/`wmctrl` on Linux or
  `osascript` on macOS) and finally falls back to the process name if a PID is
  known.
- Text elements inside the focused window on Windows.
- Clipboard changes in real time.
- Keyboard and mouse activity.
- Optional file modifications using `watchdog`.

If the `keyboard` or `mouse` packages are unavailable, `SystemMonitor` falls
back to local `keyboard_stub` and `mouse_stub` modules that provide no-op
`hook` functions. These stubs allow the code and tests to run without the
optional input libraries installed.

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

Snapshots from the `SystemMonitor` are silently appended to the conversation as
extra context. They no longer trigger automatic replies. To see a quick recap
of the latest snapshot, type **summary** in the text box and the assistant will
respond with a short overview.

`ClippyAgent` normally sends short summaries periodically. Passing
`notify_interval=None` when creating the agent disables this behavior so you
don't see duplicate messages if another bot handles notifications.

### Custom system prompt

`OllamaClient` now accepts a `system_prompt` argument. This optional string
sets the initial system message used for every conversation. If omitted, the
client defaults to "You are a helpful assistant." Passing a different value lets
you customize the assistant's personality.

Use `OllamaClient.add_context(text)` to append additional system messages
without making an API request. `ClippyAgent` relies on this to feed each
system snapshot into the conversation history.

## Memos and process scans

Use `SystemMonitor.save_screen_memo()` to capture on-screen text and save it in the `ai_memos` folder. The helper `memo_utils.save_memo()` writes a timestamped file with a descriptive name. Typing **memo**, **remember**, or **note** in the assistant's text box automatically triggers this capture. Pass `allow_empty=True` to `save_screen_memo` to force a memo even when OCR text can't be captured (e.g. if dependencies are missing).

`SystemMonitor.scan_processes()` performs a simple heuristic check for suspicious processes based on keywords like "malware" or "virus".

## Google Voice assistant

The optional `google_voice_assistant.py` script automates texting through
Google Voice. It defaults to running Chrome in headless mode. Set the
environment variable `HEADLESS=0` to open a visible browser window so you
can complete login or any verification steps.

## Discord Bot
Run `discord_bot.py` to enable a chat interface in Discord.
Set the `DISCORD_TOKEN` environment variable with your bot token before running.
The bot requires the **Message Content Intent** to read text in channels, so
enable that permission in the Discord developer portal.

The bot also starts a small `SystemMonitor` thread. Type `!status` in any channel
to see a summary of recent window titles, inputs, and clipboard changes.

## Optional packages for GUI and screenshot features

The minimal `requirements.txt` keeps dependencies small. Install these extras to enable the graphical interface and screenshot capture:

- `PyQt5` for the desktop GUI
- `pyautogui` or `Pillow` to take screenshots
- `pytesseract` for OCR on those images
- `watchdog`, `pyperclip`, `pygetwindow`, and `pywin32` improve monitoring when present

The test suite automatically skips GUI and screenshot features when these packages are missing.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
