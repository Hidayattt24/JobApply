"""CV text -> structured candidate profile via AI."""

from __future__ import annotations

from app.ai.base import AIService
from app.ai.prompts import CV_PARSE_SYSTEM, cv_parse_prompt
from app.ai.schemas import CandidateProfileData
from app.profile.parser import extract_text


def parse_cv_to_profile(ai: AIService, file_path: str) -> CandidateProfileData:
    text = extract_text(file_path)
    prompt = cv_parse_prompt(text)
    return ai.generate_json(prompt, CandidateProfileData, system=CV_PARSE_SYSTEM)
