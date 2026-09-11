"""Email content and factuality validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ai.schemas import Fact

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}|\[\[.*?\]\]|<.*?>")
YEARS_RE = re.compile(r"\b\d+\s*(?:\+|plus)?\s*(?:years?|yrs|tahun)\b", re.IGNORECASE)
METRIC_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|x|times|users?|requests?|clients?|apps?|projects?)\b",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_recipient(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def validate_inputs(company: str, position: str, recipient_email: str) -> ValidationResult:
    result = ValidationResult()
    if not company or not company.strip():
        result.errors.append("Company is empty.")
    if not position or not position.strip():
        result.errors.append("Position is empty.")
    if not validate_recipient(recipient_email):
        result.errors.append(f"Invalid recipient email format: {recipient_email!r}.")
    result.passed = not result.errors
    return result


def validate_body(
    body: str, candidate_name: str, company: str, position: str
) -> ValidationResult:
    result = ValidationResult()
    if not body or not body.strip():
        result.errors.append("Email body is empty.")
        result.passed = False
        return result

    if PLACEHOLDER_RE.search(body):
        result.errors.append("Email body contains unresolved placeholders.")

    if candidate_name and candidate_name.lower() not in body.lower():
        result.errors.append("Email body does not mention the candidate name.")

    if company and company.lower() not in body.lower():
        result.errors.append("Email body does not mention the target company.")

    if position and position.lower() not in body.lower():
        result.errors.append("Email body does not mention the target position.")

    result.passed = not result.errors
    return result


def validate_factuality(body: str, facts: list[Fact]) -> ValidationResult:
    result = ValidationResult()
    fact_texts = [f.text.lower() for f in facts]

    for match in YEARS_RE.finditer(body):
        claim = match.group(0)
        if not any(claim.lower() in ft for ft in fact_texts):
            result.warnings.append(
                f"Possible unverified 'years of experience' claim: {claim!r}."
            )

    for match in METRIC_RE.finditer(body):
        claim = match.group(0)
        if not any(claim.lower() in ft for ft in fact_texts):
            result.warnings.append(f"Possible unverified metric claim: {claim!r}.")

    return result


def validate_email(
    body: str,
    candidate_name: str,
    company: str,
    position: str,
    recipient_email: str,
    facts: list[Fact],
) -> ValidationResult:
    result = ValidationResult()

    inputs = validate_inputs(company, position, recipient_email)
    result.errors.extend(inputs.errors)

    body_result = validate_body(body, candidate_name, company, position)
    result.errors.extend(body_result.errors)

    fact_result = validate_factuality(body, facts)
    result.warnings.extend(fact_result.warnings)

    result.passed = not result.errors
    return result
