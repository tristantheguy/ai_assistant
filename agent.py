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
        notify_interval: int | None = None,
    ) -> None:
        self.window = window
        # Monitor the current directory for file changes as an example
        self.monitor = SystemMonitor(watch_paths=["."])
        self.llm = OllamaClient(
            system_prompt=(
                "You’re Clippy with a tsundere streak—snarky but still helpful. "
                "Offer advice grudgingly in one or two sentences."
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
                if self._last_snapshot is None:
                    changed = True
                else:
                    prev = {k: v for k, v in self._last_snapshot.items() if k != "timestamp"}
                    curr = {k: v for k, v in snapshot.items() if k != "timestamp"}
                    changed = curr != prev
                if changed:
                    summary = json.dumps(snapshot)
                    self.llm.add_context(summary)
                self._last_snapshot = snapshot
            except Exception:  # noqa: E722 - broad catch to keep thread alive
                self._report_exception()
            for _ in range(self.poll_interval):
                if self._stop.is_set():
                    break
                time.sleep(1)

    def handle_text(self, text):
        """Process text input by querying the LLM and showing the reply."""
        lower = text.lower().strip()

        if lower == "summary":
            snapshot = self._last_snapshot or self.monitor.capture_snapshot()
            reply = self.llm.query(json.dumps(snapshot))
            self.window.display_message(reply)
            return

        reply = self.llm.query(text)
        self.window.display_message(reply)

        if any(k in lower for k in ["memo", "remember", "note"]):
            try:
                self.monitor.save_screen_memo(label=text, allow_empty=True)
            except Exception:
                pass
