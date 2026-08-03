"""Shared safe test configuration and fixtures for testing."""

from __future__ import annotations

import os
import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# These values must exist before test modules import app.main or workers.celery_app.
os.environ.setdefault("APP_ENV", "test")
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "INFO"
os.environ.setdefault("EMBEDDING_DIMENSIONS", "1024")
os.environ.setdefault("SOURCE_ALLOWED_DIALECTS", "postgresql")
os.environ.setdefault("CELERY_TASK_IGNORE_RESULT", "true")

from app.config import reset_settings_cache
from app.dependencies import get_db
from app.main import app
from models.base import Base


@pytest.fixture(autouse=True)
def test_environment(monkeypatch: pytest.MonkeyPatch):
    """Force test mode so no real secrets or external services are required."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "1024")
    monkeypatch.setenv("SOURCE_ALLOWED_DIALECTS", "postgresql")
    monkeypatch.setenv("CELERY_TASK_IGNORE_RESULT", "true")
    reset_settings_cache()
    yield
    reset_settings_cache()
    os.environ.pop("APP_ENV", None)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """In-memory SQLite database session fixture with PostgreSQL function stubs."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def register_sqlite_functions(dbapi_connection, connection_record):
        dbapi_connection.create_function("uuid_generate_v4", 0, lambda: str(uuid.uuid4()))

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
