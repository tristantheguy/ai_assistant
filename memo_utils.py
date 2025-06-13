import os
from datetime import datetime

MEMO_DIR = "ai_memos"


def save_memo(text: str, label: str | None = None, directory: str = MEMO_DIR) -> str:
    """Save text to a timestamped memo file and return the path."""
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_label = "".join(c for c in (label or text[:20]) if c.isalnum() or c in ("_", " ")).strip()
    filename = f"{timestamp}_{safe_label or 'memo'}.txt".replace(" ", "_")
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path
