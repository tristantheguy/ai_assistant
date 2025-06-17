from types import SimpleNamespace
import builtins
import gmail_utils


def test_get_service(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_TOKEN_FILE", "token.json")

    calls = {}

    def fake_exists(self):
        calls["path"] = str(self)
        return True

    class DummyCreds:
        expired = False
        refresh_token = None

        def refresh(self, request):
            calls["refreshed"] = True

    fake_creds = DummyCreds()

    def fake_from_file(path, scopes):
        calls["from_file"] = path
        calls["scopes"] = scopes
        return fake_creds

    def fake_build(api, version, credentials):
        calls["credentials"] = credentials
        return "svc"

    monkeypatch.setattr(gmail_utils.Path, "exists", fake_exists)
    monkeypatch.setattr(gmail_utils.Credentials, "from_authorized_user_file", staticmethod(fake_from_file))
    monkeypatch.setattr(gmail_utils, "build", fake_build)
    monkeypatch.setattr(gmail_utils, "Request", object)

    service = gmail_utils.get_service()
    assert service == "svc"
    assert calls["credentials"] is fake_creds
    assert calls["from_file"] == "token.json"
    assert calls["scopes"] == ["https://www.googleapis.com/auth/gmail.readonly"]


def test_search_messages():
    class DummyMessages:
        def __init__(self):
            self.queries = []

        def list(self, userId="me", q=None):
            self.queries.append(q)
            return SimpleNamespace(execute=lambda: {"messages": [{"id": "1"}, {"id": "2"}]})

        def get(self, userId="me", id=None, format=None, metadataHeaders=None):
            return SimpleNamespace(execute=lambda: {"payload": {"headers": [{"name": "Subject", "value": f"sub {id}"}]}})

    class DummyUsers:
        def __init__(self):
            self.msg = DummyMessages()

        def messages(self):
            return self.msg

    class DummyService:
        def __init__(self):
            self.users_inst = DummyUsers()

        def users(self):
            return self.users_inst

    svc = DummyService()
    res = gmail_utils.search_messages(svc, "foo")
    assert svc.users_inst.msg.queries == ["foo"]
    assert res == [("1", "sub 1"), ("2", "sub 2")]
