"""Persist and load the verified candidate profile and facts."""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.schemas import (
    Achievement,
    CandidateProfileData,
    Education,
    Experience,
    Fact,
    PersonalInfo,
    Project,
)
from app.config import DATA_DIR

PROFILE_DIR = DATA_DIR / "profile"
PROFILE_FILE = PROFILE_DIR / "profile.json"
FACTS_FILE = PROFILE_DIR / "facts.json"


def profile_exists() -> bool:
    return PROFILE_FILE.exists()


def load_profile() -> CandidateProfileData:
    if not PROFILE_FILE.exists():
        raise FileNotFoundError("No candidate profile found. Run: python -m app profile import <CV>")
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return CandidateProfileData.model_validate(data)


def save_profile(profile: CandidateProfileData, verified: bool = True) -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(
        json.dumps(profile.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if verified:
        _derive_facts(profile)


def load_facts() -> list[Fact]:
    if not FACTS_FILE.exists():
        return []
    data = json.loads(FACTS_FILE.read_text(encoding="utf-8"))
    return [Fact.model_validate(item) for item in data.get("facts", [])]


def _derive_facts(profile: CandidateProfileData) -> None:
    facts: list[Fact] = []

    def add(source: str, index: int, text: str) -> None:
        if not text.strip():
            return
        facts.append(
            Fact(
                id=f"{source}-{index:03d}",
                text=text.strip(),
                source=f"{source}.json",
                verified=True,
            )
        )

    for i, exp in enumerate(profile.experiences, start=1):
        add("experience", i, f"Worked as {exp.title} at {exp.company}")

    for i, proj in enumerate(profile.projects, start=1):
        tech = ", ".join(proj.technologies) if proj.technologies else ""
        text = f"Developed {proj.name}"
        if tech:
            text += f" using {tech}"
        add("project", i, text)

    for i, ach in enumerate(profile.achievements, start=1):
        add("achievement", i, ach.text)

    for i, edu in enumerate(profile.education, start=1):
        text = f"{edu.degree}"
        if edu.university:
            text += f" from {edu.university}"
        add("education", i, text)

    FACTS_FILE.write_text(
        json.dumps({"facts": [f.model_dump() for f in facts]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_signature(profile: CandidateProfileData) -> str:
    p = profile.personal
    lines = ["Best regards,", "", p.name]
    if p.email:
        lines.append(f"Email: {p.email}")
    if p.phone:
        lines.append(f"Phone: {p.phone}")
    if p.github:
        lines.append(f"GitHub: {p.github}")
    if p.linkedin:
        lines.append(f"LinkedIn: {p.linkedin}")
    if p.website:
        lines.append(f"Website: {p.website}")
    return "\n".join(lines)
