"""Job and Application persistence + duplicate detection."""

from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    Application,
    ApplicationStatus,
    EmailLog,
    EmailLogStatus,
    Job,
)


def add_job(
    session: Session,
    company: str,
    position: str,
    recipient_email: str,
    job_description: str,
    recruiter_name: str | None = None,
    job_url: str | None = None,
    custom_subject: str | None = None,
) -> Job:
    job = Job(
        company=company,
        position=position,
        recipient_email=recipient_email,
        recruiter_name=recruiter_name,
        job_url=job_url,
        custom_subject=custom_subject,
        job_description=job_description,
    )
    session.add(job)
    session.flush()
    return job


def list_jobs(session: Session) -> list[Job]:
    return list(session.scalars(select(Job).order_by(Job.id)))


def get_job(session: Session, job_id: int) -> Job | None:
    return session.get(Job, job_id)


def create_application(session: Session, job: Job) -> Application:
    app = Application(job_id=job.id, status=ApplicationStatus.DRAFT)
    session.add(app)
    session.flush()
    return app


def get_or_create_application(session: Session, job: Job) -> Application:
    stmt = select(Application).where(Application.job_id == job.id)
    app = session.scalars(stmt).first()
    if app is None:
        return create_application(session, job)
    return app


def list_applications(session: Session) -> list[Application]:
    return list(session.scalars(select(Application).order_by(Application.id)))


def get_application(session: Session, application_id: int) -> Application | None:
    return session.get(Application, application_id)


def set_analysis(session: Session, job: Job, analysis: dict) -> None:
    job.analysis_json = json.dumps(analysis, ensure_ascii=False)


def set_match(session: Session, application: Application, match_result: dict) -> None:
    application.match_score = match_result.get("match_score")
    application.match_result_json = json.dumps(match_result, ensure_ascii=False)


def set_email(
    session: Session, application: Application, subject: str, body: str
) -> None:
    application.subject = subject
    application.body = body


def find_duplicate(session: Session, company: str, position: str, recipient_email: str) -> Application | None:
    """Return an application already SENT for the same logical key, if any."""
    stmt = (
        select(Application)
        .join(Job)
        .where(
            Job.company == company,
            Job.position == position,
            Job.recipient_email == recipient_email,
            Application.status == ApplicationStatus.SENT,
        )
    )
    return session.scalars(stmt).first()


def has_sent_log(session: Session, application: Application) -> bool:
    stmt = select(EmailLog).where(
        EmailLog.application_id == application.id,
        EmailLog.status == EmailLogStatus.SENT,
    )
    return session.scalars(stmt).first() is not None


def bulk_status(session: Session, ids: Iterable[int], status: ApplicationStatus) -> None:
    for aid in ids:
        app = session.get(Application, aid)
        if app is not None:
            app.status = status
