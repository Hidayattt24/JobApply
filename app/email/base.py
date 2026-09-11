"""Email provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SendResult:
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None


class EmailProvider(ABC):
    @abstractmethod
    def send(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
        dry_run: bool = False,
    ) -> SendResult:
        """Send an email; if ``dry_run`` is True, do not actually send."""
