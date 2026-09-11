"""Email rendering helpers and attachment validation."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

SUPPORTED_ATTACHMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_ATTACHMENT_SIZE_MB = 25


class AttachmentError(RuntimeError):
    pass


def resolve_attachment(path: str | None) -> Path | None:
    settings = get_settings()
    resolved = path or settings.default_cv_path
    if not resolved:
        return None
    return Path(resolved)


def _validate_file(attachment: Path) -> Path:
    if not attachment.exists():
        raise AttachmentError(f"Attachment does not exist: {attachment}")
    if not attachment.is_file():
        raise AttachmentError(f"Attachment is not a file: {attachment}")
    if attachment.suffix.lower() not in SUPPORTED_ATTACHMENT_EXTENSIONS:
        raise AttachmentError(
            f"Unsupported attachment extension: {attachment.suffix}. "
            f"Supported: {sorted(SUPPORTED_ATTACHMENT_EXTENSIONS)}"
        )
    size_mb = attachment.stat().st_size / (1024 * 1024)
    if size_mb > MAX_ATTACHMENT_SIZE_MB:
        raise AttachmentError(
            f"Attachment too large: {size_mb:.1f}MB (max {MAX_ATTACHMENT_SIZE_MB}MB)."
        )
    return attachment


def validate_attachment(path: str | None) -> Path | None:
    attachment = resolve_attachment(path)
    if attachment is None:
        return None
    return _validate_file(attachment)


def resolve_portfolio() -> Path | None:
    """Return the validated portfolio PDF path, or None if not configured/invalid.

    Used both at generation time (to decide whether the email mentions the
    portfolio) and at send time (to attach it), so the two always agree.
    """
    settings = get_settings()
    path = settings.default_portfolio_path
    if not path:
        return None

    try:
        return _validate_file(Path(path))
    except AttachmentError as exc:
        logger.warning("Portfolio not attached: %s", exc)
        return None
