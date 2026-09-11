"""Application configuration loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    timezone: str = "Asia/Jakarta"
    default_cv_path: str = "data/attachments/Hidayat_Nur_Hakim_CV.pdf"
    default_portfolio_path: str = ""

    # AI
    ai_provider: str = "gemini"
    ai_api_key: str = ""
    ai_model: str = "gemini-2.5-flash"
    ai_temperature: float = 0.4

    # Email
    email_provider: str = "gmail"
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = "http://localhost"
    gmail_sender_email: str = ""
    gmail_token_file: str = "data/auth/gmail_token.json"
    email_dry_run: bool = False

    # Database
    database_url: str = "sqlite:///data/jobapply.db"

    # Scheduler
    default_schedule_time: str = "08:00"

    # Safety
    max_emails_per_batch: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_dirs() -> None:
    for sub in ("profile", "cv", "attachments", "auth", "db"):
        (DATA_DIR / sub).mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
