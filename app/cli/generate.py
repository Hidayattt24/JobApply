"""Generate personalized emails via AI."""

from __future__ import annotations

from app.cli._common import (
    console,
    get_ai_or_exit,
    load_profile_or_exit,
    open_session,
    select_jobs,
)
from app.database.models import ApplicationStatus
from app.jobs import repository as jobs_repo
from app.workflow import generate_one, validate_application


def generate_emails(job_ids: str | None = None, all_flag: bool = False) -> None:
    """Generate personalized emails for selected jobs."""
    ai = get_ai_or_exit()
    profile = load_profile_or_exit()
    session = open_session()
    try:
        jobs = jobs_repo.list_jobs(session)
        selected = select_jobs(session, jobs, "Generate", job_ids, all_flag)
        if not selected:
            return

        generated = 0
        for job in selected:
            application = jobs_repo.get_or_create_application(session, job)
            console.print(
                f"Generating email for [bold]{job.company}[/bold] - {job.position}..."
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
