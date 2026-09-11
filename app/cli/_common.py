"""Shared helpers for CLI commands."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session

from app.ai.base import AIService, AIServiceError
from app.ai.gemini_provider import get_ai_service
from app.ai.schemas import CandidateProfileData
from app.database.database import get_session_factory
from app.database.models import Job
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


def parse_job_ids(selection: str) -> list[int]:
    """Parse a comma-separated job ID string into ints. Raises ValueError."""
    ids: list[int] = []
    for part in selection.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"Invalid job id: {part!r}")
        ids.append(int(part))
    return ids


def _job_status(session: Session, job: Job) -> str:
    from app.jobs.repository import get_application_for_job

    app = get_application_for_job(session, job.id)
    return app.status.value if app else "-"


def select_jobs(
    session: Session,
    jobs: list[Job],
    action: str,
    selection: str | None = None,
    all_flag: bool = False,
) -> list[Job] | None:
    """Return the jobs selected by the user.

    - ``all_flag`` -> all jobs.
    - ``selection`` -> comma-separated IDs.
    - otherwise -> interactive table + prompt (Enter cancels).
    """
    if not jobs:
        console.print("[yellow]No jobs found.[/yellow]")
        return None

    table = Table(title=f"{action}: select jobs")
    table.add_column("ID", justify="right")
    table.add_column("Company")
    table.add_column("Position")
    table.add_column("Status")
    for job in jobs:
        table.add_row(
            str(job.id), job.company, job.position, _job_status(session, job)
        )
    console.print(table)

    if all_flag:
        return jobs

    chosen = selection
    if chosen is None:
        chosen = typer.prompt(
            f"{action} - job IDs (comma-separated) or 'all', Enter to cancel",
            default="",
        ).strip()

    if chosen == "":
        console.print("[dim]Cancelled.[/dim]")
        return None

    if chosen.lower() == "all":
        return jobs

    try:
        ids = parse_job_ids(chosen)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return None

    by_id = {job.id: job for job in jobs}
    selected: list[Job] = []
    for job_id in ids:
        if job_id not in by_id:
            console.print(f"[yellow]Warning: job id {job_id} not found.[/yellow]")
            continue
        selected.append(by_id[job_id])

    return selected or None

