"""Test schedule time conversion."""

from datetime import datetime, timezone

import pytest
from typer import BadParameter

from app.cli.schedule import _to_utc


def test_to_utc():
    result = _to_utc("2026-09-15", "08:00", "Asia/Jakarta")
    assert result.tzinfo is not None
    assert result == datetime(2026, 9, 15, 1, 0, tzinfo=timezone.utc)


def test_to_utc_invalid_date():
    with pytest.raises(BadParameter):
        _to_utc("2026-13-40", "08:00", "Asia/Jakarta")


def test_to_utc_invalid_timezone():
    with pytest.raises(BadParameter):
        _to_utc("2026-09-15", "08:00", "Mars/Olympus")
