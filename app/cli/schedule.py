"""Schedule approved emails (now, 08:00, or custom time)."""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import typer
from rich.table import Table
from sqlalchemy import select

from app.cli._common import console, open_session
from app.config import get_settings
from app.database.models import Application, ApplicationStatus
from app.scheduler import service as scheduler_service
from app.send_service import send_application

schedule_app = typer.Typer(help="Schedule approved emails.")


def _approved_apps(session):
    stmt = select(Application).where(Application.status == ApplicationStatus.APPROVED)
    return list(session.scalars(stmt))


def _to_utc(local_date: str, local_time: str, tz_name: str) -> datetime:
    try:
        tz = ZoneInfo(tz_name)
    except Exception as exc:  # noqa: BLE001
        raise typer.BadParameter(f"Invalid timezone: {tz_name}") from exc

    try:
        naive = datetime.combine(
            datetime.strptime(local_date, "%Y-%m-%d").date(),
            datetime.strptime(local_time, "%H:%M").time(),
        )
    except ValueError as exc:
        raise typer.BadParameter(f"Invalid date/time: {exc}") from exc

    aware = naive.replace(tzinfo=tz)
    return aware.astimezone(timezone.utc)


@schedule_app.command("set")
def schedule_emails() -> None:
    """Schedule approved applications."""
    settings = get_settings()
    session = open_session()
    try:
        apps = _approved_apps(session)
        if not apps:
            console.print("[yellow]No approved applications to schedule.[/yellow]")
            return

        table = Table(title="Approved applications")
        table.add_column("ID", justify="right")
        table.add_column("Company")
        table.add_column("Position")
        for app in apps:
            table.add_row(str(app.id), app.job.company, app.job.position)
        console.print(table)

        console.print("\nScheduling mode:")
        console.print("[1] Send all now")
        console.print("[2] Schedule all at 08:00")
        console.print("[3] Custom time for each")
        mode = typer.prompt("Choice", type=str, default="2")

        if mode == "1":
            if not typer.confirm(f"Send {len(apps)} email(s) now?", default=False):
                console.print("[dim]Cancelled.[/dim]")
                return
            for app in apps:
                result = send_application(session, app)
                console.print(
                    f"[green]Sent to {app.job.company}[/green]"
                    if result.ok
                    else f"[red]Failed: {app.job.company} — {result.error}[/red]"
                )
            session.commit()
            return

        if mode == "2":
            date_str = typer.prompt("Date", default="")
            time_str = settings.default_schedule_time
        elif mode == "3":
            date_str = typer.prompt("Date", default="")
            time_str = typer.prompt("Time", default=settings.default_schedule_time)
        else:
            console.print("[red]Invalid choice.[/red]")
            raise typer.Exit(1)

        scheduled_at = _to_utc(date_str, time_str, settings.timezone)
        for app in apps:
            scheduler_service.create_schedule(
                session, app.id, scheduled_at, settings.timezone
            )
        session.commit()

        console.print(
            f"[green]{len(apps)} application(s) scheduled at "
            f"{date_str} {time_str} {settings.timezone}.[/green]"
        )
        console.print(
            "[dim]Run 'python -m app scheduler-run' to start the scheduler daemon.[/dim]"
        )
    finally:
        session.close()
