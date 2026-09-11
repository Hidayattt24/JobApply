"""Job description analysis via AI."""

from __future__ import annotations

from app.ai.base import AIService
from app.ai.prompts import JD_ANALYZE_SYSTEM, jd_analyze_prompt
from app.ai.schemas import JobAnalysis


def analyze_job(
    ai: AIService, company: str, position: str, job_description: str
) -> JobAnalysis:
    prompt = jd_analyze_prompt(company, position, job_description)
    return ai.generate_json(prompt, JobAnalysis, system=JD_ANALYZE_SYSTEM)
