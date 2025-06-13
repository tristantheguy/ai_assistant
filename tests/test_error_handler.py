import json
import os
import builtins
from unittest import mock
from error_handler import ErrorReporter


def test_handle_exception_writes_log(tmp_path):
    log_file = tmp_path / "err.txt"
    reporter = ErrorReporter(log_path=str(log_file), memory=3)

    fake_response = mock.Mock()
    fake_response.json.return_value = {"message": {"content": "oops"}}
    fake_response.headers = {"content-type": "application/json"}
    fake_response.raise_for_status.return_value = None

    with mock.patch("requests.post", return_value=fake_response):
        try:
            raise ValueError("bad")
        except Exception:
            reporter.handle_exception()

    assert log_file.exists()
    text = log_file.read_text()
    assert "ValueError" in text
    assert "oops" in text

    # Ensure memory deque keeps messages within limit
    assert len(reporter._messages) <= 3

