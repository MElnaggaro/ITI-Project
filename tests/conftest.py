"""Shared safe test configuration for the Phase 01 foundation."""

from __future__ import annotations

import os

import pytest

# These values must exist before test modules import app.main or workers.celery_app.
os.environ.setdefault("APP_ENV", "test")
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "INFO"
os.environ.setdefault("EMBEDDING_DIMENSIONS", "1024")
os.environ.setdefault("SOURCE_ALLOWED_DIALECTS", "postgresql")
os.environ.setdefault("CELERY_TASK_IGNORE_RESULT", "true")

from app.config import reset_settings_cache


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
