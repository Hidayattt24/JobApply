"""Orchestrates sending a single approved application."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.models import (
    Application,
    ApplicationStatus,
    EmailLog,
    EmailLogStatus,
)
from app.email.base import SendResult
from app.email.renderer import resolve_portfolio, validate_attachment
from app.email.sender import get_email_provider
from app.logging_config import get_logger

logger = get_logger(__name__)


def send_application(
    session: Session,
    application: Application,
    attachment_path: str | None = None,
    dry_run: bool | None = None,
) -> SendResult:
    settings = get_settings()
    if dry_run is None:
        dry_run = settings.email_dry_run

    job = application.job
    if not application.subject or not application.body:
        return SendResult(ok=False, error="Application has no generated email.")

    cv = validate_attachment(attachment_path)
    portfolio = resolve_portfolio()
    attachments = [a for a in (cv, portfolio) if a is not None]

    application.status = ApplicationStatus.SENDING
    session.flush()

    provider = get_email_provider()
    result = provider.send(
        to=job.recipient_email,
        subject=application.subject,
        body=application.body,
        attachments=attachments or None,
        dry_run=dry_run,
    )

    if result.ok:
        if dry_run:
            log_status = EmailLogStatus.DRY_RUN
            application.status = ApplicationStatus.APPROVED
        else:
            log_status = EmailLogStatus.SENT
            application.status = ApplicationStatus.SENT
    else:
        log_status = EmailLogStatus.FAILED
        application.status = ApplicationStatus.FAILED

    session.add(
        EmailLog(
            application_id=application.id,
            provider_message_id=result.provider_message_id,
            status=log_status,
            error_message=result.error,
        )
    )
    session.flush()
    return result
