"""Test profile repository and database models."""

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.schemas import (
    CandidateProfileData,
    Education,
    Experience,
    PersonalInfo,
    Project,
)
from app.database.models import ApplicationStatus, Base, Job
from app.jobs.repository import (
    add_job,
    find_duplicate,
    get_or_create_application,
)
from app.profile import repository as profile_repo


def _make_profile() -> CandidateProfileData:
    return CandidateProfileData(
        personal=PersonalInfo(name="Hidayat Nur Hakim", email="h@example.com"),
        education=[Education(degree="Bachelor of Informatics", university="USK")],
        skills=["React", "TypeScript"],
        experiences=[Experience(title="AI Engineer Intern", company="Diskominsa Aceh")],
        projects=[Project(name="LawChain", technologies=["FastAPI", "FAISS"])],
    )


def test_save_and_load_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(profile_repo, "PROFILE_FILE", tmp_path / "profile.json")
    monkeypatch.setattr(profile_repo, "FACTS_FILE", tmp_path / "facts.json")

    profile = _make_profile()
    profile_repo.save_profile(profile, verified=True)

    loaded = profile_repo.load_profile()
    assert loaded.personal.name == "Hidayat Nur Hakim"
    assert loaded.skills == ["React", "TypeScript"]

    facts = profile_repo.load_facts()
    assert any("Diskominsa Aceh" in f.text for f in facts)
    assert any("LawChain" in f.text for f in facts)


def test_signature(tmp_path, monkeypatch):
    monkeypatch.setattr(profile_repo, "PROFILE_FILE", tmp_path / "profile.json")
    monkeypatch.setattr(profile_repo, "FACTS_FILE", tmp_path / "facts.json")
    profile = _make_profile()
    sig = profile_repo.build_signature(profile)
    assert "Hidayat Nur Hakim" in sig
    assert "h@example.com" in sig


def test_job_and_application_flow():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()

    job = add_job(
        session,
        company="ABC",
        position="Dev",
        recipient_email="hr@abc.com",
        job_description="Build apps",
    )
    session.commit()

    app = get_or_create_application(session, job)
    assert app.status == ApplicationStatus.DRAFT

    app.status = ApplicationStatus.SENT
    session.commit()

    dup = find_duplicate(session, "ABC", "Dev", "hr@abc.com")
    assert dup is not None

    none = find_duplicate(session, "XYZ", "Dev", "hr@abc.com")
    assert none is None

    session.close()
