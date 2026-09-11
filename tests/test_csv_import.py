"""Test CSV bulk import."""

import pytest

from app.jobs.csv_import import CSVImportError, parse_jobs_csv


def test_parse_valid_csv(tmp_path):
    path = tmp_path / "jobs.csv"
    path.write_text(
        "company,position,email,recruiter,job_url,job_description\n"
        "ABC,Frontend Developer,hr@abc.com,Rina,,Build web apps\n"
        "XYZ,AI Engineer,hr@xyz.com,,https://x.com/j/1,Do ML\n",
        encoding="utf-8",
    )
    rows = parse_jobs_csv(str(path))
    assert len(rows) == 2
    assert rows[0]["company"] == "ABC"
    assert rows[0]["recruiter_name"] == "Rina"
    assert rows[1]["recruiter_name"] is None


def test_missing_columns(tmp_path):
    path = tmp_path / "jobs.csv"
    path.write_text("company,position\nABC,Dev\n", encoding="utf-8")
    with pytest.raises(CSVImportError):
        parse_jobs_csv(str(path))


def test_missing_file():
    with pytest.raises(CSVImportError):
        parse_jobs_csv("does-not-exist.csv")


def test_required_field_empty(tmp_path):
    path = tmp_path / "jobs.csv"
    path.write_text(
        "company,position,email,job_description\n,Dev,hr@x.com,desc\n",
        encoding="utf-8",
    )
    with pytest.raises(CSVImportError):
        parse_jobs_csv(str(path))
