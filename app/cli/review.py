"""Review, approve, edit, or regenerate application emails."""

from __future__ import annotations

import typer
from rich.panel import Panel
from sqlalchemy import select

from app.ai.schemas import CandidateProfileData
from app.cli._common import (
    console,
    edit_text,
    get_ai_or_exit,
    load_profile_or_exit,
    open_session,
)
from app.database.models import Application, ApplicationStatus
from app.jobs import repository as jobs_repo
from app.workflow import generate_one

review_app = typer.Typer(help="Review generated emails before sending.")


def _display(application: Application) -> None:
    job = application.job
    console.rule(f"Application #{application.id}")
    console.print(f"Company:   {job.company}")
    console.print(f"Position:  {job.position}")
    console.print(f"Match:     {application.match_score or 0}%")
    console.print(f"Subject:   {application.subject or ''}")
    console.print(Panel(application.body or "", title="EMAIL BODY"))


def _select_targets(session, all_flag: bool) -> list[Application]:
    stmt = select(Application).order_by(Application.id)
    apps = list(session.scalars(stmt))
    if not all_flag:
        apps = [a for a in apps if a.status == ApplicationStatus.REVIEW_REQUIRED]
    return apps


@review_app.command("list")
def review_emails(
    all_flag: bool = typer.Option(False, "--all", help="Review all applications."),
) -> None:
    """Review applications one by one."""
    session = open_session()
    try:
        targets = _select_targets(session, all_flag)
        if not targets:
            console.print("[yellow]No applications to review.[/yellow]")
            return

        ai = None
        profile: CandidateProfileData | None = None

        total = len(targets)
        for idx, application in enumerate(targets, start=1):
            _display(application)
            console.print(f"\n[yellow]{idx}/{total}[/yellow]")
            console.print("[1] Approve  [2] Edit  [3] Regenerate  [4] Skip  [5] Back")
            choice = typer.prompt("Action", type=str, default="1")

            if choice == "1":
                application.status = ApplicationStatus.APPROVED
                session.commit()
                console.print("[green]Approved.[/green]")
            elif choice == "2":
                _edit(session, application)
            elif choice == "3":
                if ai is None:
                    ai = get_ai_or_exit()
                    profile = load_profile_or_exit()
                console.print("Regenerating...")
                assert profile is not None
                generate_one(session, ai, application, profile)
                application.status = ApplicationStatus.REVIEW_REQUIRED
                session.commit()
                _display(application)
            elif choice == "4":
                application.status = ApplicationStatus.SKIPPED
                session.commit()
                console.print("[dim]Skipped.[/dim]")
            elif choice == "5":
                console.print("[dim]Stopping review.[/dim]")
                break
            else:
                console.print("[yellow]Unknown action, skipping.[/yellow]")

        session.commit()
    finally:
        session.close()


def _edit(session, application: Application) -> None:
    subject = typer.prompt(
        "Subject", default=application.subject or ""
    )
    console.print("Edit body in your editor. Save & close to apply.")
    body = edit_text(application.body or "")
    if body is None:
        console.print("[yellow]Edit cancelled.[/yellow]")
        return
    jobs_repo.set_email(session, application, subject, body)
    application.status = ApplicationStatus.REVIEW_REQUIRED
    session.commit()
    console.print("[green]Email updated.[/green]")
