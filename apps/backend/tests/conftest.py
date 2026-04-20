from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_engine
from app.db.session import get_session_factory
from app.db.session import reset_database_state
from app.main import create_application


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

    get_settings.cache_clear()
    reset_database_state()
    Base.metadata.create_all(bind=get_engine())

    yield

    Base.metadata.drop_all(bind=get_engine())
    reset_database_state()
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    application = create_application()

    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Session:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
