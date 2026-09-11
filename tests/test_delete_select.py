"""Tests for job deletion and job-ID selection parsing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.cli._common import parse_job_ids
from app.database.models import (
    Application,
    ApplicationStatus,
    Base,
    Schedule,
    ScheduleStatus,
)
from app.jobs.repository import (
    add_job,
    create_application,
    delete_all_jobs,
    delete_job,
    get_application_for_job,
)


def _make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True, expire_on_commit=False)()


# --- parse_job_ids ---------------------------------------------------------

def test_parse_job_ids_valid():
    assert parse_job_ids("1,2,3") == [1, 2, 3]
    assert parse_job_ids(" 1 , 5 ") == [1, 5]
    assert parse_job_ids("") == []


def test_parse_job_ids_invalid():
    with pytest.raises(ValueError):
        parse_job_ids("1,abc")


# --- delete_job + cascade --------------------------------------------------

def test_delete_job_cascades_application_and_schedule():
    session = _make_session()
    job = add_job(
        session,
        company="ABC",
        position="Dev",
        recipient_email="hr@abc.com",
        job_description="Build apps",
    )
    app = create_application(session, job)
    schedule = Schedule(
        application_id=app.id,
        scheduled_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        status=ScheduleStatus.PENDING,
    )
    session.add(schedule)
    session.commit()

    assert delete_job(session, job.id) is True
    session.commit()

    assert get_application_for_job(session, job.id) is None
    assert session.get(Application, app.id) is None
    assert session.get(Schedule, schedule.id) is None
    session.close()


def test_delete_job_missing_returns_false():
    session = _make_session()
    assert delete_job(session, 999) is False
    session.close()


def test_delete_all_jobs():
    session = _make_session()
    for i in range(3):
        add_job(
            session,
            company=f"C{i}",
            position="Dev",
            recipient_email=f"hr{i}@x.com",
            job_description="Build",
        )
    session.commit()

    assert delete_all_jobs(session) == 3
    session.commit()

    from app.jobs.repository import list_jobs

    assert list_jobs(session) == []
    session.close()


def test_get_application_for_job_none_when_missing():
    session = _make_session()
    assert get_application_for_job(session, 999) is None
    session.close()
