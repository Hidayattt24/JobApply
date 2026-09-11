"""Tests for Gmail OAuth authentication (mocked)."""

import pytest

from app.email import auth as gmail_auth
from app.email.auth import (
    GmailAuthError,
    NOT_AUTHENTICATED_MSG,
    NOT_CONFIGURED_MSG,
    REVOKED_MSG,
)


class FakeSettings:
    def __init__(self, client_id="", client_secret="", token_file="data/auth/gmail_token.json"):
        self.gmail_client_id = client_id
        self.gmail_client_secret = client_secret
        self.gmail_token_file = token_file


class FakeCreds:
    def __init__(self, valid=True, expired=False, refresh_token="rt", refresh_ok=True):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refresh_ok = refresh_ok
        self.refreshed = False

    def refresh(self, request):
        self.refreshed = True
        if not self.refresh_ok:
            raise RuntimeError("revoked")


class FakeRefreshError(Exception):
    pass


@pytest.fixture
def patch_auth(monkeypatch):
    def _patch(settings=None, creds=None, refresh_error=FakeRefreshError):
        monkeypatch.setattr(gmail_auth, "get_settings", lambda: settings or FakeSettings())
        monkeypatch.setattr(gmail_auth, "load_credentials", lambda: creds)
        monkeypatch.setattr(
            gmail_auth,
            "_import_google",
            lambda: (refresh_error, object, FakeCreds, object),
        )
        monkeypatch.setattr(gmail_auth, "_save_credentials", lambda c: None)

    return _patch


def test_oauth_not_configured(patch_auth):
    patch_auth(settings=FakeSettings())
    with pytest.raises(GmailAuthError) as exc:
        gmail_auth.get_credentials()
    assert "not configured" in str(exc.value).lower()
    assert "GMAIL_CLIENT_ID" in str(exc.value)


def test_token_missing(patch_auth):
    patch_auth(settings=FakeSettings(client_id="cid", client_secret="csec"), creds=None)
    with pytest.raises(GmailAuthError) as exc:
        gmail_auth.get_credentials()
    assert str(exc.value) == NOT_AUTHENTICATED_MSG


def test_valid_token(patch_auth):
    creds = FakeCreds(valid=True)
    patch_auth(settings=FakeSettings(client_id="cid", client_secret="csec"), creds=creds)
    result = gmail_auth.get_credentials()
    assert result is creds
    assert creds.refreshed is False


def test_expired_token_refreshes(patch_auth):
    creds = FakeCreds(valid=False, expired=True, refresh_token="rt")
    patch_auth(settings=FakeSettings(client_id="cid", client_secret="csec"), creds=creds)
    result = gmail_auth.get_credentials()
    assert result is creds
    assert creds.refreshed is True


def test_revoked_refresh_token(patch_auth):
    creds = FakeCreds(valid=False, expired=True, refresh_token="rt", refresh_ok=False)
    patch_auth(settings=FakeSettings(client_id="cid", client_secret="csec"), creds=creds)
    with pytest.raises(GmailAuthError) as exc:
        gmail_auth.get_credentials()
    assert str(exc.value) == REVOKED_MSG


def test_status_authenticated(patch_auth, monkeypatch):
    creds = FakeCreds(valid=True)
    patch_auth(settings=FakeSettings(client_id="cid", client_secret="csec"), creds=creds)
    monkeypatch.setattr(gmail_auth, "get_authenticated_email", lambda c: "me@gmail.com")
    state = gmail_auth.status()
    assert state["authenticated"] is True
    assert state["email"] == "me@gmail.com"


def test_error_messages_do_not_leak_secret():
    secret = "super-secret-client-secret"
    for msg in (NOT_CONFIGURED_MSG, NOT_AUTHENTICATED_MSG, REVOKED_MSG):
        assert secret not in msg
