"""Send approved emails now."""

from __future__ import annotations

import typer
from rich.table import Table
from sqlalchemy import select

from app.cli._common import console, open_session
from app.config import get_settings
from app.database.models import Application, ApplicationStatus
from app.jobs import repository as jobs_repo
from app.send_service import send_application

send_app = typer.Typer(help="Send approved emails.")


@send_app.command("now")
def send_now(
    all_flag: bool = typer.Option(False, "--all", help="Send all approved applications."),
) -> None:
    """Send approved applications immediately."""
    settings = get_settings()
    session = open_session()
    try:
        stmt = select(Application).where(
            Application.status == ApplicationStatus.APPROVED
        )
        apps = list(session.scalars(stmt))
        if not apps:
            console.print("[yellow]No approved applications to send.[/yellow]")
            return

        if len(apps) > settings.max_emails_per_batch:
            console.print(
                f"[red]Batch contains {len(apps)} emails. "
                f"Configured maximum is {settings.max_emails_per_batch}.[/red]"
            )
            console.print("[red]Operation blocked.[/red]")
            raise typer.Exit(1)

        table = Table(title="Ready to send")
        table.add_column("ID", justify="right")
        table.add_column("Company")
        table.add_column("Position")
        table.add_column("To")
        for app in apps:
            table.add_row(str(app.id), app.job.company, app.job.position, app.job.recipient_email)
        console.print(table)

        if settings.email_dry_run:
            console.print("[yellow]DRY RUN mode is enabled — emails will NOT be sent.[/yellow]")

        if not typer.confirm(
            f"You are about to send {len(apps)} email(s). Continue?", default=False
        ):
            console.print("[dim]Cancelled.[/dim]")
            return

        sent = 0
        failed = 0
        for app in apps:
            duplicate = jobs_repo.find_duplicate(
                session, app.job.company, app.job.position, app.job.recipient_email
            )
            if duplicate and duplicate.id != app.id:
                console.print(
                    f"[yellow]Warning: application for {app.job.company} — "
                    f"{app.job.position} already sent ({duplicate.id}). Skipping.[/yellow]"
                )
                continue

            result = send_application(session, app)
            if result.ok:
                console.print(f"[green]Sent to {app.job.company} ({app.job.recipient_email})[/green]")
                sent += 1
            else:
                console.print(f"[red]Failed: {app.job.company} — {result.error}[/red]")
                failed += 1

        session.commit()
        console.print(f"[bold]{sent} sent, {failed} failed.[/bold]")
    finally:
        session.close()
