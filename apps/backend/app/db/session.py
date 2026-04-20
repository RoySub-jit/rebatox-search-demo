from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _engine_options(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }

    return {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.sqlalchemy_database_uri,
            echo=settings.sqlalchemy_echo,
            future=True,
            **_engine_options(settings.sqlalchemy_database_uri),
        )

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    return _session_factory


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def reset_database_state() -> None:
    global _engine
    global _session_factory

    if _engine is not None:
        _engine.dispose()

    _engine = None
    _session_factory = None
