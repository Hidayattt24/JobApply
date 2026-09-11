"""High-level workflow orchestration shared across CLI commands."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai.analyzer import analyze_job
from app.ai.base import AIService
from app.ai.generator import generate_email
from app.ai.matcher import match_candidate
from app.ai.schemas import CandidateProfileData, EmailDraft, JobAnalysis, MatchResult
from app.database.models import Application, ApplicationStatus, Job
from app.email.renderer import resolve_portfolio
from app.jobs.repository import (
    get_or_create_application,
    set_analysis,
    set_email,
    set_match,
)
from app.logging_config import get_logger
from app.profile.repository import build_signature
from app.validation.email_validator import validate_email

logger = get_logger(__name__)


def analyze_one(session: Session, ai: AIService, job: Job) -> JobAnalysis:
    analysis = analyze_job(ai, job.company, job.position, job.job_description)
    set_analysis(session, job, analysis.model_dump())
    application = get_or_create_application(session, job)
    application.status = ApplicationStatus.ANALYZING
    session.flush()
    return analysis


def generate_one(
    session: Session,
    ai: AIService,
    application: Application,
    profile: CandidateProfileData,
) -> tuple[EmailDraft, JobAnalysis, MatchResult]:
    job = application.job

    if not job.analysis_json:
        analysis = analyze_one(session, ai, job)
    else:
        analysis = JobAnalysis.model_validate(json.loads(job.analysis_json))

    match_result = match_candidate(ai, analysis, profile)
    set_match(session, application, match_result.model_dump())

    signature = build_signature(profile)
    has_portfolio = resolve_portfolio() is not None
    draft = generate_email(
        ai,
        company=job.company,
        position=job.position,
        recruiter_name=job.recruiter_name,
        job_analysis=analysis,
        match_result=match_result,
        profile=profile,
        signature=signature,
        has_portfolio=has_portfolio,
    )
    subject = (job.custom_subject or "").strip() or draft.subject
    set_email(session, application, subject, draft.body)
    application.status = ApplicationStatus.GENERATED
    session.flush()

    return draft, analysis, match_result


def validate_application(
    application: Application, profile: CandidateProfileData
) -> tuple[bool, list[str], list[str]]:
    from app.profile.repository import load_facts

    job = application.job
    facts = load_facts()
    result = validate_email(
        body=application.body or "",
        candidate_name=profile.personal.name,
        company=job.company,
        position=job.position,
        recipient_email=job.recipient_email,
        facts=facts,
    )
    if result.passed:
        application.status = ApplicationStatus.VALIDATED
    else:
        application.status = ApplicationStatus.REVIEW_REQUIRED
    return result.passed, result.errors, result.warnings
