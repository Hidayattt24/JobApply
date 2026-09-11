"""Gmail email sending via the Gmail API."""

from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path

from app.config import get_settings
from app.email.auth import GmailAuthError, get_authenticated_email, get_credentials
from app.email.base import EmailProvider, SendResult
from app.logging_config import get_logger

logger = get_logger(__name__)


class SenderMismatchError(GmailAuthError):
    pass


class GmailSender(EmailProvider):
    def __init__(self, service=None) -> None:
        self._service = service

    def _get_service(self):
        if self._service is None:
            from app.email.client import get_gmail_service

            self._service = get_gmail_service()
        return self._service

    def _verify_sender(self, sender: str) -> None:
        """Ensure the authenticated account matches GMAIL_SENDER_EMAIL."""
        creds = get_credentials()
        try:
            authenticated = get_authenticated_email(creds)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not resolve authenticated email: %s", type(exc).__name__)
            return

        if authenticated and authenticated.lower() != sender.lower():
            raise SenderMismatchError(
                f"Authenticated Gmail account ({authenticated}) does not match "
                f"GMAIL_SENDER_EMAIL ({sender}). Fix GMAIL_SENDER_EMAIL and retry."
            )

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
        dry_run: bool = False,
    ) -> SendResult:
        settings = get_settings()
        sender = settings.gmail_sender_email
        if not sender:
            return SendResult(ok=False, error="GMAIL_SENDER_EMAIL is not set in .env")

        if dry_run:
            logger.info("DRY RUN: email to %s was NOT sent.", to)
            return SendResult(ok=True, provider_message_id="dry-run")

        try:
            self._verify_sender(sender)
            message = self._build_mime_message(sender, to, subject, body, attachments)
            service = self._get_service()
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
            result = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute()
            )
            message_id = result.get("id")
            logger.info("Email sent to %s (message id: %s)", to, message_id)
            return SendResult(ok=True, provider_message_id=message_id)
        except GmailAuthError as exc:
            logger.warning("Gmail send blocked: %s", type(exc).__name__)
            return SendResult(ok=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error("Gmail send failed: %s", type(exc).__name__)
            return SendResult(ok=False, error="Gmail API error: email was not sent.")

    @staticmethod
    def _build_mime_message(
        sender: str,
        to: str,
        subject: str,
        body: str,
        attachments: list[Path] | None,
    ) -> EmailMessage:
        message = EmailMessage()
        message["To"] = to
        message["From"] = sender
        message["Subject"] = subject
        message.set_content(body)

        for path in attachments or []:
            if not path.exists():
                continue
            mime_type = "application/octet-stream"
            if path.suffix.lower() == ".pdf":
                mime_type = "application/pdf"
            elif path.suffix.lower() == ".docx":
                mime_type = (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
            message.add_attachment(
                path.read_bytes(),
                maintype=mime_type.split("/")[0],
                subtype=mime_type.split("/")[1],
                filename=path.name,
            )

        return message


def get_email_provider() -> EmailProvider:
    settings = get_settings()
    provider = settings.email_provider.lower()
    if provider == "gmail":
        return GmailSender()
    from app.email.auth import GmailAuthError

    raise GmailAuthError(f"Unsupported email provider: {provider}")
