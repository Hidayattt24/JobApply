"""Tests for Gmail sender / MIME construction (mocked Gmail API)."""

import base64
from pathlib import Path

import pytest

from app.email.auth import GmailAuthError
from app.email.sender import GmailSender, SenderMismatchError


class FakeSettings:
    def __init__(self, sender_email="me@gmail.com", dry_run=False):
        self.gmail_sender_email = sender_email
        self.email_dry_run = dry_run


class FakeMessages:
    def __init__(self, result=None, error=None):
        self._result = result if result is not None else {"id": "msg123"}
        self._error = error

    def send(self, userId, body):
        return self

    def execute(self):
        if self._error:
            raise self._error
        return self._result


class FakeService:
    def __init__(self, messages):
        self._messages = messages

    def users(self):
        return self

    def messages(self):
        return self._messages


@pytest.fixture
def patch_sender(monkeypatch):
    def _patch(settings=None, email="me@gmail.com", creds=None):
        monkeypatch.setattr(
            "app.email.sender.get_settings",
            lambda: settings or FakeSettings(),
        )
        monkeypatch.setattr("app.email.sender.get_credentials", lambda: creds or object())
        monkeypatch.setattr("app.email.sender.get_authenticated_email", lambda c: email)

    return _patch


def test_mime_creation(tmp_path):
    attachment = tmp_path / "cv.pdf"
    attachment.write_bytes(b"%PDF-1.4 fake content")

    message = GmailSender._build_mime_message(
        sender="me@gmail.com",
        to="hr@abc.com",
        subject="Application for Dev",
        body="Dear Hiring Team,\n\nI am applying.",
        attachments=[attachment],
    )

    assert message["To"] == "hr@abc.com"
    assert message["From"] == "me@gmail.com"
    assert message["Subject"] == "Application for Dev"

    parts = list(message.iter_attachments())
    assert len(parts) == 1
    assert parts[0].get_filename() == "cv.pdf"


def test_send_success(patch_sender):
    messages = FakeMessages(result={"id": "msg123"})
    sender = GmailSender(service=FakeService(messages))
    patch_sender(settings=FakeSettings(sender_email="me@gmail.com"), email="me@gmail.com")

    result = sender.send(to="hr@abc.com", subject="Subj", body="Body")

    assert result.ok is True
    assert result.provider_message_id == "msg123"


def test_send_api_error(patch_sender):
    messages = FakeMessages(error=RuntimeError("boom"))
    sender = GmailSender(service=FakeService(messages))
    patch_sender(settings=FakeSettings(sender_email="me@gmail.com"), email="me@gmail.com")

    result = sender.send(to="hr@abc.com", subject="Subj", body="Body")

    assert result.ok is False
    assert "API error" in result.error
    assert "boom" not in result.error


def test_sender_mismatch_blocks_send(patch_sender):
    sender = GmailSender(service=FakeService(FakeMessages()))
    patch_sender(
        settings=FakeSettings(sender_email="me@gmail.com"),
        email="other@gmail.com",
    )

    result = sender.send(to="hr@abc.com", subject="Subj", body="Body")

    assert result.ok is False
    assert "does not match" in result.error


def test_dry_run_does_not_send(patch_sender):
    messages = FakeMessages()
    sender = GmailSender(service=FakeService(messages))
    patch_sender(settings=FakeSettings(sender_email="me@gmail.com", dry_run=True))

    result = sender.send(to="hr@abc.com", subject="Subj", body="Body", dry_run=True)

    assert result.ok is True
    assert result.provider_message_id == "dry-run"
