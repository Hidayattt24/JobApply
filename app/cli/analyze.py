"""Analyze job descriptions via AI."""

from __future__ import annotations

from app.cli._common import console, get_ai_or_exit, open_session
from app.jobs import repository as jobs_repo
from app.workflow import analyze_one


def analyze_jobs() -> None:
    """Analyze all job descriptions and store the result."""
    ai = get_ai_or_exit()
    session = open_session()
    try:
        jobs = jobs_repo.list_jobs(session)
        if not jobs:
            console.print("[yellow]No jobs to analyze.[/yellow]")
            return

        for job in jobs:
            console.print(f"Analyzing [bold]{job.company}[/bold] — {job.position}...")
            analyze_one(session, ai, job)

        session.commit()
        console.print(f"[green]{len(jobs)} job(s) analyzed.[/green]")
    finally:
        session.close()
