"""Personalized email generation via AI."""

from __future__ import annotations

from app.ai.base import AIService
from app.ai.prompts import EMAIL_SYSTEM, email_prompt
from app.ai.schemas import (
    CandidateProfileData,
    EmailDraft,
    JobAnalysis,
    MatchResult,
)


def generate_email(
    ai: AIService,
    company: str,
    position: str,
    recruiter_name: str | None,
    job_analysis: JobAnalysis,
    match_result: MatchResult,
    profile: CandidateProfileData,
    signature: str,
    has_portfolio: bool = False,
) -> EmailDraft:
    prompt = email_prompt(
        company=company,
        position=position,
        recruiter_name=recruiter_name,
        job_analysis=job_analysis.model_dump(),
        match_result=match_result.model_dump(),
        profile=profile,
        signature=signature,
        has_portfolio=has_portfolio,
    )
    return ai.generate_json(prompt, EmailDraft, system=EMAIL_SYSTEM)
