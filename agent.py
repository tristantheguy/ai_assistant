import threading
import time

from system_monitor import SystemMonitor
from llm_client import OllamaClient

class ClippyAgent:
    """Core logic combining monitoring, LLM querying and UI updates."""

    def __init__(self, window, poll_interval=10):
        self.window = window
        # Monitor the current directory for file changes as an example
        self.monitor = SystemMonitor(watch_paths=["."])
        self.llm = OllamaClient()
        self.poll_interval = poll_interval
        self._stop = threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()
        self.thread.join()

    def _loop(self):
        while not self._stop.is_set():
            self.monitor.capture_snapshot()
            summary = self.monitor.summarize()
            response = self.llm.query(summary)
            self.window.display_message(response)
            for _ in range(self.poll_interval):
                if self._stop.is_set():
                    break
                time.sleep(1)
