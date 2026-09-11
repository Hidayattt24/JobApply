"""Database engine and session management."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.models import Base

_engine = None
_SessionLocal = None


def _make_engine():
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        if not path.startswith("/"):
            path = path
    return create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        future=True,
    )


def get_engine():
    global _engine
    if _engine is None:
        _engine = _make_engine()
    return _engine


def _migrate(engine) -> None:
    """Lightweight additive migrations for SQLite (existing dev DBs)."""
    if engine.url.get_backend_name() != "sqlite":
        return

    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return

    existing = {c["name"] for c in inspector.get_columns("jobs")}
    if "custom_subject" not in existing:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN custom_subject TEXT"))


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        _migrate(engine)
        _SessionLocal = sessionmaker(
            bind=engine, autoflush=False, expire_on_commit=False, future=True
        )
    return _SessionLocal


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _migrate(engine)


def session_scope():
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
