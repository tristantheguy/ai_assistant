import importlib
import os
from pathlib import Path
import pytest


def test_default_folder_resolves(monkeypatch):
    pytest.importorskip("PyQt5")
    monkeypatch.delenv("AI_ASSISTANT_FOLDER", raising=False)
    import gui_interface
    importlib.reload(gui_interface)
    assert gui_interface.FOLDER_PATH == Path.home() / "Documents" / "AI Assistant"

