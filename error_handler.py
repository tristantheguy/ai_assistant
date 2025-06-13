import json
import traceback
from collections import deque
from datetime import datetime
from typing import Deque, Dict, Any

import requests


class ErrorReporter:
    """Send exceptions to an LLM and log the explanation."""

    def __init__(
        self,
        model: str = "dolphin-mixtral:8x7b",
        url: str = "http://localhost:11434/api/chat",
        log_path: str = "error_report.txt",
        memory: int = 6,
    ) -> None:
        self.model = model
        self.url = url
        self.log_path = log_path
        self._messages: Deque[Dict[str, Any]] = deque(maxlen=memory)
        self._messages.append(
            {
                "role": "system",
                "content": "You help explain Python exceptions succinctly.",
            }
        )

    def _query_llm(self, error: str) -> str:
        self._messages.append({"role": "user", "content": f"Explain this Python error:\n{error}"})
        payload = {"model": self.model, "messages": list(self._messages)}
        try:
            resp = requests.post(self.url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("message", {}).get("content", "")
        except Exception as exc:  # noqa: E722 - broad catch to avoid recursion
            reply = f"Failed to query LLM: {exc}"
        self._messages.append({"role": "assistant", "content": reply})
        return reply

    def handle_exception(self) -> None:
        err = traceback.format_exc()
        explanation = self._query_llm(err)
        print(explanation)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                ts = datetime.now().isoformat()
                f.write(f"--- {ts} ---\n{err}\n{explanation}\n\n")
        except Exception:
            pass

