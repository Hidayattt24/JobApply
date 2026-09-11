"""Analyze job descriptions via AI."""

from __future__ import annotations

from app.cli._common import console, get_ai_or_exit, open_session, select_jobs
from app.jobs import repository as jobs_repo
from app.workflow import analyze_one


def analyze_jobs(job_ids: str | None = None, all_flag: bool = False) -> None:
    """Analyze selected job descriptions and store the results."""
    ai = get_ai_or_exit()
    session = open_session()
    try:
        jobs = jobs_repo.list_jobs(session)
        selected = select_jobs(session, jobs, "Analyze", job_ids, all_flag)
        if not selected:
            return

        for job in selected:
            console.print(f"Analyzing [bold]{job.company}[/bold] - {job.position}...")
            analyze_one(session, ai, job)

        session.commit()
        console.print(f"[green]{len(selected)} job(s) analyzed.[/green]")
    finally:
        session.close()
