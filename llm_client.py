import json
import requests

class OllamaClient:
    def __init__(self, model="openhermes", url="http://localhost:11434/api/chat"):
        self.model = model
        self.url = url

    def query(self, prompt, timeout=60):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
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
        return data.get("message", {}).get("content", "")
