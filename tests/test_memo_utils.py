import os
from memo_utils import save_memo


def test_save_memo_creates_file(tmp_path):
    path = save_memo("hello world", "greeting", directory=tmp_path)
    assert os.path.exists(path)
    text = open(path, "r", encoding="utf-8").read()
    assert "hello world" in text
