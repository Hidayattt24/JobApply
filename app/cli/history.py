"""View application and email history."""

from __future__ import annotations

import typer
from rich.table import Table
from sqlalchemy import select

from app.cli._common import console, open_session
from app.database.models import EmailLog
from app.jobs import repository as jobs_repo

history_app = typer.Typer(help="View application history.")


@history_app.command("list")
def list_history() -> None:
    """Show application history with status and email logs."""
    session = open_session()
    try:
        apps = jobs_repo.list_applications(session)
        if not apps:
            console.print("[yellow]No applications found.[/yellow]")
            return

        table = Table(title="Applications")
        table.add_column("ID", justify="right")
        table.add_column("Company")
        table.add_column("Position")
        table.add_column("Match", justify="right")
        table.add_column("Status")
        for app in apps:
            table.add_row(
                str(app.id),
                app.job.company,
                app.job.position,
                f"{app.match_score or 0}%",
                app.status.value,
            )
        console.print(table)

        logs = list(
            session.scalars(
                select(EmailLog).order_by(EmailLog.sent_at.desc()).limit(20)
            )
        )
        if logs:
            log_table = Table(title="Recent Email Logs")
            log_table.add_column("App ID", justify="right")
            log_table.add_column("Status")
            log_table.add_column("Sent At")
            log_table.add_column("Message ID")
            for log in logs:
                log_table.add_row(
                    str(log.application_id),
                    log.status.value,
                    str(log.sent_at),
                    log.provider_message_id or "",
                )
            console.print(log_table)
    finally:
        session.close()
