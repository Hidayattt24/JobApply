"""Job CLI commands."""

from __future__ import annotations

import typer
from rich.table import Table

from app.cli._common import console, open_session
from app.jobs.csv_import import CSVImportError, parse_jobs_csv
from app.jobs import repository as jobs_repo

jobs_app = typer.Typer(help="Manage job applications.")


@jobs_app.command("add")
def add_jobs() -> None:
    """Interactively add one or more job applications."""
    session = open_session()
    try:
        count = typer.prompt("How many applications?", type=int, default=1)
        if count < 1:
            console.print("[red]Must add at least 1 job.[/red]")
            raise typer.Exit(1)

        for i in range(1, count + 1):
            console.rule(f"Application {i}/{count}")
            company = typer.prompt("Company")
            position = typer.prompt("Position")
            email = typer.prompt("Recipient email")
            recruiter = typer.prompt("Recruiter name (optional)", default="")
            job_url = typer.prompt("Job URL (optional)", default="")
            subject = typer.prompt("Email subject (optional, AI generates if empty)", default="")
            description = typer.prompt("Job Description")

            jobs_repo.add_job(
                session,
                company=company,
                position=position,
                recipient_email=email,
                recruiter_name=recruiter or None,
                job_url=job_url or None,
                custom_subject=subject or None,
                job_description=description,
            )

        session.commit()
        console.print(f"[green]{count} job(s) added successfully.[/green]")
    finally:
        session.close()


@jobs_app.command("import")
def import_jobs(
    csv_path: str = typer.Argument(..., help="Path to jobs CSV file."),
) -> None:
    """Bulk import jobs from a CSV file."""
    try:
        rows = parse_jobs_csv(csv_path)
    except CSVImportError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    session = open_session()
    try:
        for row in rows:
            jobs_repo.add_job(session, **row)
        session.commit()
        console.print(f"[green]{len(rows)} job(s) imported successfully.[/green]")
    finally:
        session.close()


@jobs_app.command("list")
def list_jobs() -> None:
    """List all jobs."""
    session = open_session()
    try:
        jobs = jobs_repo.list_jobs(session)
        if not jobs:
            console.print("[yellow]No jobs found.[/yellow]")
            return

        table = Table(title="Jobs")
        table.add_column("ID", justify="right")
        table.add_column("Company")
        table.add_column("Position")
        table.add_column("Email")
        table.add_column("Recruiter")
        for job in jobs:
            table.add_row(
                str(job.id),
                job.company,
                job.position,
                job.recipient_email,
                job.recruiter_name or "",
            )
        console.print(table)
    finally:
        session.close()
