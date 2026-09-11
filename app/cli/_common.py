"""Shared helpers for CLI commands."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from rich.console import Console
from sqlalchemy.orm import Session

from app.ai.base import AIService, AIServiceError
from app.ai.gemini_provider import get_ai_service
from app.ai.schemas import CandidateProfileData
from app.database.database import get_session_factory
from app.profile import repository as profile_repo

console = Console()


def open_session() -> Session:
    return get_session_factory()()


def get_ai() -> AIService:
    return get_ai_service()


def get_ai_or_exit() -> AIService:
    try:
        return get_ai()
    except AIServiceError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


def load_profile_or_exit() -> CandidateProfileData:
    try:
        return profile_repo.load_profile()
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)


def edit_text(text: str) -> str | None:
    """Open ``text`` in the user's editor and return the edited text.

    Returns None if editing could not be started (treated as cancel).
    """
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="jobapply_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)

        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if editor:
            cmd = [editor, path]
        elif os.name == "nt":
            cmd = ["notepad", path]
        else:
            cmd = ["vi", path]

        subprocess.call(cmd)

        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        console.print(f"[yellow]Could not open editor: {exc}[/yellow]")
        return None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

