"""CSV bulk import of jobs."""

from __future__ import annotations

import csv
from pathlib import Path

REQUIRED_COLUMNS = ["company", "position", "email", "job_description"]


class CSVImportError(RuntimeError):
    pass


def parse_jobs_csv(file_path: str) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        raise CSVImportError(f"File does not exist: {file_path}")

    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise CSVImportError("CSV has no header row.")

        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise CSVImportError(f"Missing required columns: {missing}")

        rows: list[dict] = []
        for i, row in enumerate(reader, start=2):
            job = {
                "company": (row.get("company") or "").strip(),
                "position": (row.get("position") or "").strip(),
                "recipient_email": (row.get("email") or "").strip(),
                "recruiter_name": (row.get("recruiter") or "").strip() or None,
                "job_url": (row.get("job_url") or "").strip() or None,
                "custom_subject": (row.get("subject") or "").strip() or None,
                "job_description": (row.get("job_description") or "").strip(),
            }
            if not job["company"] or not job["position"] or not job["recipient_email"]:
                raise CSVImportError(
                    f"Row {i}: company, position, and email are required."
                )
            if not job["job_description"]:
                raise CSVImportError(f"Row {i}: job_description is required.")
            rows.append(job)

    if not rows:
        raise CSVImportError("CSV contains no job rows.")
    return rows
