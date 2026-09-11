"""Prompt templates for the AI pipeline."""

from __future__ import annotations

import json

from app.ai.schemas import CandidateProfileData

SYSTEM_RULES = """You are an application email assistant.

Use only verified candidate facts.

Never invent:
- experience
- skills
- technologies
- years of experience
- achievements
- metrics
- employment history

If a fact is not available, omit it. Do not mention it."""

CV_PARSE_SYSTEM = """You extract structured data from a candidate's CV/resume text.
Be precise and factual. Only extract information explicitly present in the text.
Do not infer, guess, or fabricate any detail. If a field is absent, leave it empty.
For the 'website' field, extract the candidate's portfolio/personal website URL if
it is present (otherwise leave empty)."""

JD_ANALYZE_SYSTEM = """You analyze a job description and extract structured requirements.
Only use information explicitly present in the job description text."""

MATCH_SYSTEM = """You compare job requirements against a candidate's verified profile.
Match score (0-100) is informational only. Never fabricate a candidate's skills or
experience to improve the score."""

EMAIL_SYSTEM = SYSTEM_RULES


def cv_parse_prompt(cv_text: str) -> str:
    return (
        "Extract the candidate's profile from the CV text below and return JSON "
        "matching the schema.\n\nCV TEXT:\n"
        + cv_text
    )


def jd_analyze_prompt(company: str, position: str, job_description: str) -> str:
    return (
        f"Analyze the following job description.\n\n"
        f"Company: {company}\nPosition: {position}\n\n"
        f"Job Description:\n{job_description}"
    )


def match_prompt(job_analysis: dict, profile: CandidateProfileData) -> str:
    profile_json = json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)
    return (
        "Compare the job requirements with the candidate's verified profile.\n\n"
        f"JOB ANALYSIS:\n{json.dumps(job_analysis, ensure_ascii=False, indent=2)}\n\n"
        f"CANDIDATE PROFILE:\n{profile_json}"
    )


def email_prompt(
    company: str,
    position: str,
    recruiter_name: str | None,
    job_analysis: dict,
    match_result: dict,
    profile: CandidateProfileData,
    signature: str,
    has_portfolio: bool = False,
) -> str:
    profile_json = json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)
    portfolio_instruction = ""
    if has_portfolio:
        portfolio_instruction = (
            "\nA portfolio PDF is attached to this email. Mention it naturally in "
            "one sentence (e.g., 'I have also attached my portfolio for your "
            "review.'). Do not describe or invent the portfolio's contents, as you "
            "do not have access to them.\n"
        )
    return (
        "Write a personalized application email based on the context below.\n\n"
        f"Company: {company}\n"
        f"Position: {position}\n"
        f"Recruiter name: {recruiter_name or ''}\n\n"
        "Salutation rules:\n"
        f"- If a recruiter name is provided, start with 'Dear {recruiter_name},'.\n"
        f"- If no recruiter name is provided, start with 'Dear HRD / Hiring Team {company},'.\n"
        "Do not write 'Dear Hiring Team' without the company name.\n\n"
        f"JOB ANALYSIS:\n{json.dumps(job_analysis, ensure_ascii=False, indent=2)}\n\n"
        f"MATCH RESULT:\n{json.dumps(match_result, ensure_ascii=False, indent=2)}\n\n"
        f"CANDIDATE VERIFIED PROFILE:\n{profile_json}\n"
        f"{portfolio_instruction}\n"
        "The email must be professional, natural, concise, and relevant to the position.\n"
        "Do not repeat the entire CV. Mention only the most relevant experience.\n"
        "Write in plain text only: no Markdown, no asterisks, no bold (no ** or #).\n"
        "End the email with this exact signature block:\n\n"
        f"{signature}\n"
    )
