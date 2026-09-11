"""Gmail API service initialization."""

from __future__ import annotations

from app.email.auth import get_credentials


def get_gmail_service():
    """Build and return an authenticated Gmail API service resource."""
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover
        from app.email.auth import GmailAuthError

        raise GmailAuthError(
            "google-api-python-client missing. Run: pip install -r requirements.txt"
        ) from exc

    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)
