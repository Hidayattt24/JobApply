"""Candidate-job matching via AI."""

from __future__ import annotations

from app.ai.base import AIService
from app.ai.prompts import MATCH_SYSTEM, match_prompt
from app.ai.schemas import CandidateProfileData, JobAnalysis, MatchResult


def match_candidate(
    ai: AIService,
    job_analysis: JobAnalysis,
    profile: CandidateProfileData,
) -> MatchResult:
    prompt = match_prompt(job_analysis.model_dump(), profile)
    return ai.generate_json(prompt, MatchResult, system=MATCH_SYSTEM)
