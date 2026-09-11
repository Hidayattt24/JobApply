"""Test email and input validation."""

from app.ai.schemas import Fact
from app.validation.email_validator import (
    validate_body,
    validate_factuality,
    validate_inputs,
    validate_recipient,
)


def test_recipient_valid():
    assert validate_recipient("hr@abc.com")
    assert validate_recipient("a.b+c@example.co.id")
    assert not validate_recipient("not-an-email")
    assert not validate_recipient("")
    assert not validate_recipient("a@b")


def test_inputs_required():
    result = validate_inputs("", "Dev", "bad")
    assert not result.passed
    assert any("Company" in e for e in result.errors)
    assert any("email" in e for e in result.errors)


def test_body_checks():
    result = validate_body(
        "Dear Hiring Team, I am applying for the Developer role at ABC.",
        candidate_name="Hidayat Nur Hakim",
        company="ABC",
        position="Developer",
    )
    assert not result.passed
    assert any("candidate name" in e for e in result.errors)


def test_body_passes():
    result = validate_body(
        "I am Hidayat Nur Hakim applying for Developer at ABC.",
        candidate_name="Hidayat Nur Hakim",
        company="ABC",
        position="Developer",
    )
    assert result.passed


def test_placeholder_detected():
    result = validate_body(
        "Hello {{name}}, applying for Developer at ABC.",
        candidate_name="Hidayat Nur Hakim",
        company="ABC",
        position="Developer",
    )
    assert any("placeholder" in e for e in result.errors)


def test_factuality_flags_unknown_years():
    facts = [Fact(id="e-1", text="Worked as Dev at X", source="experiences.json")]
    result = validate_factuality("I have 5 years of experience.", facts)
    assert any("years" in w for w in result.warnings)


def test_factuality_no_flag_for_known_metric():
    facts = [Fact(id="e-1", text="Improved performance by 30%", source="a.json")]
    result = validate_factuality("I improved performance by 30%.", facts)
    assert not result.warnings
