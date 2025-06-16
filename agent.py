import threading
import time
import json
import sys
import traceback

from system_monitor import SystemMonitor
from llm_client import OllamaClient
from error_handler import ErrorReporter

class ClippyAgent:
    """Core logic combining monitoring, LLM querying and UI updates."""

    def __init__(
        self,
        window,
        poll_interval: int = 10,
        error_reporter: ErrorReporter | None = None,
        notify_interval: int | None = 60,
    ) -> None:
        self.window = window
        # Monitor the current directory for file changes as an example
        self.monitor = SystemMonitor(watch_paths=["."])
        self.llm = OllamaClient(
            system_prompt=(
                "You are Clippy, the quirky paperclip assistant from the 90s. "
                "Give short, playful tips in a lighthearted tone. "
                "Keep responses under two sentences and avoid repeating yourself."
            )
        )
        self.poll_interval = poll_interval
        self.notify_interval = notify_interval
        self._last_snapshot: dict | None = None
        self._last_message_time = 0.0
        self._stop = threading.Event()
        self._reporter = error_reporter

    def _report_exception(self) -> None:
        """Log current exception using the reporter if available."""
        if self._reporter is not None:
            try:
                self._reporter.handle_exception()
            except Exception:
                traceback.print_exc(file=sys.stderr)
        else:
            traceback.print_exc(file=sys.stderr)

    def start(self):
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()
        self.thread.join()

    def _loop(self):
        while not self._stop.is_set():
            try:
                snapshot = self.monitor.capture_snapshot()
                now = time.time()
                if self._last_snapshot is None:
                    changed = True
                else:
                    prev = {k: v for k, v in self._last_snapshot.items() if k != "timestamp"}
                    curr = {k: v for k, v in snapshot.items() if k != "timestamp"}
                    changed = curr != prev
                timed_out = (
                    self.notify_interval is not None
                    and now - self._last_message_time >= self.notify_interval
                )

                if changed or timed_out:
                    summary = json.dumps(snapshot)
                    response = self.llm.query(summary)
                    self.window.display_message(response)
                    self._last_message_time = now
                self._last_snapshot = snapshot
            except Exception:  # noqa: E722 - broad catch to keep thread alive
                self._report_exception()
            for _ in range(self.poll_interval):
                if self._stop.is_set():
                    break
                time.sleep(1)

    def handle_text(self, text):
        """Process text input by querying the LLM and showing the reply."""
        reply = self.llm.query(text)
        self.window.display_message(reply)

        lower = text.lower()
        if any(k in lower for k in ["memo", "remember", "note"]):
            try:
                self.monitor.save_screen_memo(label=text, allow_empty=True)
            except Exception:
                pass
