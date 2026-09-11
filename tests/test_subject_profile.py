"""Tests for custom subject, signature formatting, and greeting instructions."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.prompts import email_prompt
from app.ai.schemas import CandidateProfileData, PersonalInfo
from app.database.models import Base
from app.jobs.repository import add_job
from app.profile.repository import build_signature


def _profile() -> CandidateProfileData:
    return CandidateProfileData(
        personal=PersonalInfo(
            name="Hidayat Nur Hakim",
            email="h@example.com",
            github="https://github.com/me",
            linkedin="https://linkedin.com/in/me",
            website="https://me.dev",
        ),
        skills=["React", "TypeScript"],
    )


def test_signature_has_no_markdown_and_includes_website():
    sig = build_signature(_profile())
    assert "**" not in sig
    assert "Website: https://me.dev" in sig
    assert "GitHub: https://github.com/me" in sig
    assert "LinkedIn: https://linkedin.com/in/me" in sig


def test_personal_info_has_website_default():
    info = PersonalInfo()
    assert info.website == ""


def test_email_prompt_has_hrd_greeting_and_no_markdown():
    prompt = email_prompt(
        company="PT ABC",
        position="Dev",
        recruiter_name=None,
        job_analysis={},
        match_result={},
        profile=_profile(),
        signature="Best regards",
        has_portfolio=False,
    )
    assert "Dear HRD / Hiring Team" in prompt
    assert "no Markdown" in prompt or "plain text" in prompt


def test_add_job_stores_custom_subject():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()

    job = add_job(
        session,
        company="ABC",
        position="Dev",
        recipient_email="hr@abc.com",
        job_description="Build apps",
        custom_subject="Application for Dev at ABC",
    )
    session.commit()

    assert job.custom_subject == "Application for Dev at ABC"

    none_job = add_job(
        session,
        company="XYZ",
        position="Dev",
        recipient_email="hr@xyz.com",
        job_description="Build apps",
    )
    assert none_job.custom_subject is None

    session.close()
