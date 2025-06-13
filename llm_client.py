import json
from collections import deque
from typing import Deque, Dict, Any

import requests

class OllamaClient:
    """Simple client that keeps short conversation history."""

    def __init__(
        self,
        model: str = "openhermes",
        url: str = "http://localhost:11434/api/chat",
        memory: int = 5,
        system_prompt: str = "You are a helpful assistant.",
    ) -> None:
        self.model = model
        self.url = url
        self._messages: Deque[Dict[str, Any]] = deque(maxlen=memory)
        self._messages.append({"role": "system", "content": system_prompt})

    def query(self, prompt: str, timeout: int = 60) -> str:
        """Send a prompt and update conversation history."""
        self._messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": list(self._messages)}

        resp = requests.post(self.url, json=payload, timeout=timeout)
        resp.raise_for_status()

        if "application/json" not in resp.headers.get("content-type", ""):
            parts = []
            for line in resp.text.splitlines():
                try:
                    data = json.loads(line)
                    msg = data.get("message", {}).get("content", "")
                    parts.append(msg)
                except json.JSONDecodeError:
                    continue
            return "".join(parts)

        data = resp.json()
        reply = data.get("message", {}).get("content", "")
        self._messages.append({"role": "assistant", "content": reply})
        return reply
