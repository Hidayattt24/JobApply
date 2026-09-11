"""Pydantic schemas used for AI structured output and internal data flow."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    github: str = ""
    linkedin: str = ""
    website: str = ""
    location: str = ""


class Education(BaseModel):
    degree: str = ""
    university: str = ""
    gpa: str = ""
    start_year: str = ""
    end_year: str = ""


class Experience(BaseModel):
    title: str = ""
    company: str = ""
    start: str = ""
    end: str = ""
    description: str = ""


class Project(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class Achievement(BaseModel):
    text: str = ""


class Fact(BaseModel):
    id: str
    text: str
    source: str
    verified: bool = True


class CandidateProfileData(BaseModel):
    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)


class JobAnalysis(BaseModel):
    company: str = ""
    position: str = ""
    seniority: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    match_score: int = 0
    matched_skills: list[str] = Field(default_factory=list)
    relevant_experiences: list[str] = Field(default_factory=list)
    relevant_projects: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)


class EmailDraft(BaseModel):
    subject: str = ""
    body: str = ""
    used_facts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
