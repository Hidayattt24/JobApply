"""Centralized logging configuration.

Security: third-party HTTP/OAuth libraries are silenced to WARNING so that
access tokens, refresh tokens, and client secrets are never written to the
console or log files.
"""

from __future__ import annotations

import logging
import sys

from app.config import LOGS_DIR, get_settings

_CONFIGURED = False

# Libraries that log raw HTTP requests/responses (which can contain tokens and
# client secrets). Their output is suppressed below the WARNING level.
_SENSITIVE_LOGGERS = (
    "googleapiclient",
    "google_auth_oauthlib",
    "google_auth_httplib2",
    "google.auth",
    "google.oauth2",
    "requests_oauthlib",
    "oauthlib",
    "requests",
    "urllib3",
    "httpx",
    "httpcore",
)


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)


def _configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    settings = get_settings()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    # Enable DEBUG for our own code in development only.
    if settings.app_env == "development":
        logging.getLogger("app").setLevel(logging.DEBUG)

    # Never let third-party HTTP/OAuth libraries log below WARNING.
    for name in _SENSITIVE_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
        logging.getLogger(name).propagate = False
