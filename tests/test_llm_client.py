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


def test_default_system_prompt():
    client = OllamaClient()
    assert client._messages[0]["content"] == "You are a helpful assistant."


def test_custom_system_prompt():
    client = OllamaClient(system_prompt="be quirky")
    assert client._messages[0]["content"] == "be quirky"


def test_stream_response_appends(monkeypatch):
    client = OllamaClient()

    streamed_lines = [
        json.dumps({"message": {"content": "hello "}}),
        json.dumps({"message": {"content": "world"}}),
    ]

    fake_response = mock.Mock()
    fake_response.text = "\n".join(streamed_lines)
    fake_response.headers = {"content-type": "text/event-stream"}
    fake_response.raise_for_status.return_value = None

    with mock.patch("requests.post", return_value=fake_response):
        reply = client.query("hi")

    assert reply == "hello world"
    assert client._messages[-1] == {"role": "assistant", "content": "hello world"}
