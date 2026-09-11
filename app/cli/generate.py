"""Generate personalized emails via AI."""

from __future__ import annotations

from app.cli._common import console, get_ai_or_exit, load_profile_or_exit, open_session
from app.database.models import ApplicationStatus
from app.jobs import repository as jobs_repo
from app.workflow import generate_one, validate_application


def generate_emails() -> None:
    """Generate personalized emails for all jobs."""
    ai = get_ai_or_exit()
    profile = load_profile_or_exit()
    session = open_session()
    try:
        jobs = jobs_repo.list_jobs(session)
        if not jobs:
            console.print("[yellow]No jobs to generate emails for.[/yellow]")
            return

        generated = 0
        for job in jobs:
            application = jobs_repo.get_or_create_application(session, job)
            console.print(
                f"Generating email for [bold]{job.company}[/bold] — {job.position}..."
            )
            generate_one(session, ai, application, profile)
            validate_application(application, profile)
            if application.status == ApplicationStatus.VALIDATED:
                application.status = ApplicationStatus.REVIEW_REQUIRED
            generated += 1

        session.commit()
        console.print(f"[green]{generated} email(s) generated.[/green]")
    finally:
        session.close()
