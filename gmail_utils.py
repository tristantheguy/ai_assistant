import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_service():
    """Return an authenticated Gmail API service instance.

    OAuth credentials are loaded from the path specified by
    ``GMAIL_TOKEN_FILE`` or ``gmail_token.json`` by default.
    """

    token_file = os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")

    if not Path(token_file).exists():
        raise RuntimeError(f"OAuth token file not found: {token_file}")

    creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(token_file).write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def search_messages(service, query: str):
    """Return a list of ``(id, subject)`` tuples matching ``query``."""
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    output = []
    for msg in messages:
        mid = msg.get("id")
        if not mid:
            continue
        meta = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=mid,
                format="metadata",
                metadataHeaders=["Subject"],
            )
            .execute()
        )
        headers = meta.get("payload", {}).get("headers", [])
        subject = next(
            (h["value"] for h in headers if h.get("name") == "Subject"), ""
        )
        output.append((mid, subject))
    return output
