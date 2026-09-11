"""Persistent scheduling service backed by the database."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_session_factory
from app.database.models import (
    Application,
    ApplicationStatus,
    Schedule,
    ScheduleStatus,
)
from app.logging_config import get_logger
from app.send_service import send_application

logger = get_logger(__name__)


def create_schedule(
    session: Session,
    application_id: int,
    scheduled_at: datetime,
    tz_name: str,
) -> Schedule:
    if scheduled_at.tzinfo is None:
        raise ValueError("scheduled_at must be timezone-aware.")

    schedule = Schedule(
        application_id=application_id,
        scheduled_at=scheduled_at,
        timezone=tz_name,
        status=ScheduleStatus.PENDING,
    )
    session.add(schedule)

    application = session.get(Application, application_id)
    if application is not None:
        application.status = ApplicationStatus.SCHEDULED

    session.flush()
    return schedule


def list_schedules(session: Session) -> list[Schedule]:
    return list(session.scalars(select(Schedule).order_by(Schedule.scheduled_at)))


def _due_schedules(session: Session) -> list[Schedule]:
    now = datetime.now(timezone.utc)
    stmt = select(Schedule).where(
        Schedule.status == ScheduleStatus.PENDING,
        Schedule.scheduled_at <= now,
    )
    return list(session.scalars(stmt))


def process_due(session: Session) -> list[dict]:
    results: list[dict] = []
    for schedule in _due_schedules(session):
        application = session.get(Application, schedule.application_id)
        if application is None or application.status != ApplicationStatus.SCHEDULED:
            continue

        logger.info(
            "Sending scheduled application %s (job id %s)",
            application.id,
            application.job_id,
        )
        result = send_application(session, application)

        if result.ok:
            schedule.status = ScheduleStatus.DONE
        else:
            schedule.status = ScheduleStatus.FAILED

        results.append(
            {
                "application_id": application.id,
                "ok": result.ok,
                "error": result.error,
            }
        )
    session.flush()
    return results


def run_worker_once() -> list[dict]:
    factory = get_session_factory()
    session = factory()
    try:
        return process_due(session)
    finally:
        session.close()


def start_daemon(interval_seconds: int = 30) -> None:
    """Run a blocking scheduler that periodically processes due schedules."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("APScheduler is not installed.") from exc

    logger.info("Starting scheduler daemon (interval %ss)...", interval_seconds)
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_worker_once, "interval", seconds=interval_seconds)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
