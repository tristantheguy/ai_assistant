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
- `SystemMonitor.list_open_windows()` enumerates titles of all visible windows
  using `pygetwindow` when available. It falls back to `pywinauto` on Windows,
  `wmctrl -l` on Linux, or `osascript` on macOS.

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
don't see duplicate messages if another bot handles notifications. The default
is `None`, so periodic summaries are disabled unless you opt in with a custom
interval.

### Custom system prompt

`OllamaClient` now accepts a `system_prompt` argument. This optional string
sets the initial system message used for every conversation. If omitted, the
client defaults to "You are a helpful assistant." Passing a different value lets
you customize the assistant's personality. `ClippyAgent` uses a snarky
tsundere style by default:

```
You’re Clippy with a tsundere streak—snarky but still helpful. Offer advice
grudgingly in one or two sentences.
```

Use `OllamaClient.add_context(text)` to append additional system messages
without making an API request. `ClippyAgent` relies on this to feed each
system snapshot into the conversation history.

## Memos and process scans

Use `SystemMonitor.save_screen_memo()` to capture on-screen text and save it in the `ai_memos` folder. The helper `memo_utils.save_memo()` writes a timestamped file with a descriptive name. Typing **memo**, **remember**, or **note** in the assistant's text box automatically triggers this capture. Pass `allow_empty=True` to `save_screen_memo` to force a memo even when OCR text can't be captured (e.g. if dependencies are missing).


`SystemMonitor.scan_processes()` performs a simple heuristic check for suspicious processes based on keywords like "malware" or "virus".

## Basic system control

`assistant_core.AIAssistant` understands a few shell-like commands:

- `open <path>` launches a file or folder using the default application. Use this for file or folder paths.
- `close` attempts to close the active window (requires `pyautogui` or `pywinauto`).
- `start <command>` spawns a new process via `subprocess`. Use this to run an application (e.g., `start chrome`).
- `close <title>` closes a window matching `title` when `pywinauto` is available and attempts to terminate all matching processes when possible.

These helpers live in `system_controller.py`.

## Google Voice assistant (removed)

This repository previously included a `google_voice_assistant.py` script that
automated texting through Google Voice using a headless Chrome browser. The
feature has been removed and the script no longer exists, so there is currently
no Google Voice integration.

## Discord Bot
Run `discord_bot.py` to enable a chat interface in Discord.
Set the `DISCORD_TOKEN` environment variable with your bot token before running.
The bot requires the **Message Content Intent** to read text in channels, so
enable that permission in the Discord developer portal.

The bot also starts a small `SystemMonitor` thread. Type `!status` in any channel
or ask “what’s on the screen”/“screen status” to see a summary of recent window
titles, inputs, and clipboard changes. It also recognizes simple phrases like
`open <path>`, `start <cmd>`, and `close <title>` to control the host system
directly even when the words appear mid-sentence. Use `start` for applications
(`start chrome`) and `open` for files or folders. `close <title>` attempts to
terminate all matching processes when possible.

Type `!gmail <query>` in any channel to search your Gmail inbox. The bot
authenticates using OAuth credentials stored locally. Set your Google client ID
in the `GOOGLE_CLIENT_ID` environment variable and ensure the credentials file
(`gmail_token.json` by default) is kept somewhere secure.

## Gmail OAuth Setup

To generate a valid `gmail_token.json`:

1. Create a Google Cloud project and enable the Gmail API.
2. Under **Credentials**, create an OAuth client ID for a **Desktop**
   application.
3. Download the JSON file with your client credentials (e.g.,
   `credentials.json`).
4. Run this script using `google-auth-oauthlib`:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json", ["https://www.googleapis.com/auth/gmail.readonly"]
)
creds = flow.run_local_server(port=0)
Path("gmail_token.json").write_text(creds.to_json())
```

The resulting file must contain `client_id`, `client_secret`, `refresh_token`,
and `token_uri`. Set `GOOGLE_CLIENT_ID` to the `client_id` value from the
credentials. If you store the token in a different location, point
`GMAIL_TOKEN_FILE` to that path when running the bot.

## Optional packages for GUI and screenshot features

The minimal `requirements.txt` keeps dependencies small. Install these extras to enable the graphical interface and screenshot capture:

- `PyQt5` for the desktop GUI
- `pyautogui` or `Pillow` to take screenshots
- `pytesseract` for OCR on those images
- `watchdog`, `pyperclip`, `pygetwindow`, `pywin32`, and `pywinauto` improve monitoring when present

The test suite automatically skips GUI and screenshot features when these packages are missing.

## License

This project is licensed under the terms of the [MIT License](LICENSE).
