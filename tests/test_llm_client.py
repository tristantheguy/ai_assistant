import json
from unittest import mock
from llm_client import OllamaClient


def test_memory_limit():
    client = OllamaClient(memory=3)

    fake_response = mock.Mock()
    fake_response.json.return_value = {"message": {"content": "reply"}}
    fake_response.headers = {"content-type": "application/json"}
    fake_response.raise_for_status.return_value = None

    with mock.patch("requests.post", return_value=fake_response):
        for i in range(5):
            client.query(f"msg {i}")

    # 1 system message + last 3 user/assistant pairs -> length should be <= 7
    assert len(client._messages) <= 7
