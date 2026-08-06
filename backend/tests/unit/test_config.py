"""Configuration safety tests owned by Phase 01."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_test_mode_uses_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_environment == "test"
    assert settings.embedding_dimensions == 1024
    assert settings.source_dialects == frozenset({"postgresql"})
    assert settings.celery_task_ignore_result is True


def test_invalid_embedding_dimension_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "1536")

    with pytest.raises(ValidationError, match="EMBEDDING_DIMENSIONS"):
        Settings()


def test_invalid_source_dialect_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_ALLOWED_DIALECTS", "postgresql,sqlite")

    with pytest.raises(ValidationError, match="unsupported values"):
        Settings()


def test_celery_result_persistence_cannot_be_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CELERY_TASK_IGNORE_RESULT", "false")

    with pytest.raises(ValidationError, match="CELERY_TASK_IGNORE_RESULT"):
        Settings()


def test_production_requires_real_security_material(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "REPLACE_WITH_A_SECRET")
    monkeypatch.setenv("CONNECTION_ENCRYPTION_KEY", "REPLACE_WITH_A_KEY")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "REPLACE_WITH_ACCESS")
    monkeypatch.setenv("MINIO_SECRET_KEY", "REPLACE_WITH_SECRET")

    with pytest.raises(ValidationError, match="Non-test configuration"):
        Settings()
