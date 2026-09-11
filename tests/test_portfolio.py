"""Tests for portfolio attachment and email adaptation."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.prompts import email_prompt
from app.ai.schemas import CandidateProfileData, PersonalInfo
from app.database.models import ApplicationStatus, Base, Job
from app.email.base import SendResult


class FakeSettings:
    def __init__(self, portfolio_path=""):
        self.default_portfolio_path = portfolio_path


# --- resolve_portfolio -----------------------------------------------------

def test_resolve_portfolio_empty(monkeypatch):
    from app.email import renderer

    monkeypatch.setattr(renderer, "get_settings", lambda: FakeSettings(""))
    assert renderer.resolve_portfolio() is None


def test_resolve_portfolio_missing(monkeypatch):
    from app.email import renderer

    monkeypatch.setattr(
        renderer, "get_settings", lambda: FakeSettings("nope/missing.pdf")
    )
    assert renderer.resolve_portfolio() is None


def test_resolve_portfolio_valid(tmp_path, monkeypatch):
    from app.email import renderer

    portfolio = tmp_path / "portfolio.pdf"
    portfolio.write_bytes(b"%PDF-1.4 portfolio")
    monkeypatch.setattr(
        renderer, "get_settings", lambda: FakeSettings(str(portfolio))
    )
    result = renderer.resolve_portfolio()
    assert result == portfolio


# --- email_prompt ----------------------------------------------------------

def _profile() -> CandidateProfileData:
    return CandidateProfileData(personal=PersonalInfo(name="Hidayat Nur Hakim"))


def test_email_prompt_mentions_portfolio_when_present():
    prompt = email_prompt(
        company="ABC",
        position="Dev",
        recruiter_name=None,
        job_analysis={},
        match_result={},
        profile=_profile(),
        signature="Best regards",
        has_portfolio=True,
    )
    assert "portfolio" in prompt.lower()
    assert "do not describe or invent" in prompt.lower()


def test_email_prompt_no_portfolio_when_absent():
    prompt = email_prompt(
        company="ABC",
        position="Dev",
        recruiter_name=None,
        job_analysis={},
        match_result={},
        profile=_profile(),
        signature="Best regards",
        has_portfolio=False,
    )
    assert "portfolio" not in prompt.lower()


# --- send_application multi-attachment -------------------------------------

class RecordingProvider:
    def __init__(self):
        self.attachments = None

    def send(self, to, subject, body, attachments=None, dry_run=False):
        self.attachments = attachments
        return SendResult(ok=True, provider_message_id="ok")


def test_send_application_attaches_cv_and_portfolio(monkeypatch):
    from app import send_service

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True, expire_on_commit=False)()

    job = Job(
        company="ABC",
        position="Dev",
        recipient_email="hr@abc.com",
        job_description="Build apps",
    )
    session.add(job)
    session.flush()

    from app.database.models import Application

    app = Application(job_id=job.id, status=ApplicationStatus.APPROVED)
    app.subject = "Application for Dev"
    app.body = "Dear Hiring Team, I am applying."
    session.add(app)
    session.flush()

    provider = RecordingProvider()
    monkeypatch.setattr(
        send_service, "validate_attachment", lambda path: Path("cv.pdf")
    )
    monkeypatch.setattr(
        send_service, "resolve_portfolio", lambda: Path("portfolio.pdf")
    )
    monkeypatch.setattr(send_service, "get_email_provider", lambda: provider)

    result = send_service.send_application(session, app, dry_run=False)

    assert result.ok is True
    assert provider.attachments == [Path("cv.pdf"), Path("portfolio.pdf")]
    session.close()


def test_send_application_only_cv_when_no_portfolio(monkeypatch):
    from app import send_service

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True, expire_on_commit=False)()

    job = Job(
        company="ABC",
        position="Dev",
        recipient_email="hr@abc.com",
        job_description="Build apps",
    )
    session.add(job)
    session.flush()

    from app.database.models import Application

    app = Application(job_id=job.id, status=ApplicationStatus.APPROVED)
    app.subject = "Application for Dev"
    app.body = "Dear Hiring Team."
    session.add(app)
    session.flush()

    provider = RecordingProvider()
    monkeypatch.setattr(
        send_service, "validate_attachment", lambda path: Path("cv.pdf")
    )
    monkeypatch.setattr(send_service, "resolve_portfolio", lambda: None)
    monkeypatch.setattr(send_service, "get_email_provider", lambda: provider)

    send_service.send_application(session, app, dry_run=False)

    assert provider.attachments == [Path("cv.pdf")]
    session.close()
