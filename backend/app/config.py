"""Typed, environment-driven configuration for the platform foundation."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.constants import REQUIRED_EMBEDDING_DIMENSION

EnvironmentName = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Configuration boundary; business services must consume settings, not os.environ."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FusionIsExist Platform"
    app_environment: EnvironmentName = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "APP_ENVIRONMENT"),
    )
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    debug: bool = False

    application_database_url: str = Field(
        default="postgresql+psycopg://platform:platform@postgres:5432/text_to_sql_platform",
        validation_alias=AliasChoices(
            "PLATFORM_DATABASE_URL",
            "APPLICATION_DATABASE_URL",
        ),
    )
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    celery_task_ignore_result: bool = True
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection_name: str = Field(
        default="document_chunks",
        validation_alias=AliasChoices("QDRANT_COLLECTION", "QDRANT_COLLECTION_NAME"),
    )
    qdrant_api_key: SecretStr | None = None
    qdrant_timeout_seconds: int = Field(default=10, ge=1, le=300)
    minio_endpoint: str = "minio:9000"
    minio_secure: bool = False
    minio_bucket_name: str = Field(
        default="tenant-documents",
        validation_alias=AliasChoices("MINIO_BUCKET", "MINIO_BUCKET_NAME"),
    )
    minio_access_key: str | None = None
    minio_secret_key: SecretStr | None = None

    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = Field(default=15, ge=1, le=1440)
    jwt_refresh_token_days: int = Field(default=7, ge=1, le=90)
    encryption_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("CONNECTION_ENCRYPTION_KEY", "ENCRYPTION_KEY", "ENCRYPTION_MASTER_KEY"),
    )


    llm_provider: str = "unconfigured"
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: int = Field(default=300, ge=1, le=600)
    embedding_provider: str = "unconfigured"
    embedding_model: str | None = None
    embedding_api_key: SecretStr | None = None
    embedding_batch_size: int = Field(default=32, ge=1, le=1000)
    embedding_dimensions: int = Field(
        default=REQUIRED_EMBEDDING_DIMENSION,
        ge=1,
        le=8192,
    )

    source_execution_timeout_seconds: int = Field(default=30, ge=1, le=300)
    source_query_row_limit: int = Field(default=1000, ge=1, le=10000)
    source_result_size_limit_bytes: int = Field(
        default=1_000_000,
        ge=1024,
        le=50_000_000,
    )
    metadata_sample_value_limit: int = Field(default=0, ge=0, le=100)
    query_preview_row_limit: int = Field(default=0, ge=0, le=100)
    query_preview_retention_days: int = Field(default=0, ge=0, le=3650)
    upload_size_limit_bytes: int = Field(default=25_000_000, ge=1)
    parser_timeout_seconds: int = Field(default=120, ge=1, le=3600)
    allowed_source_dialects: str = Field(
        default="postgresql",
        validation_alias=AliasChoices(
            "SOURCE_ALLOWED_DIALECTS",
            "ALLOWED_SOURCE_DIALECTS",
        ),
    )
    request_id_header: str = "X-Request-ID"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"
    cors_origins: str = ""

    prometheus_multiproc_dir: str | None = None
    otel_exporter_otlp_endpoint: str | None = None

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError("LOG_LEVEL must be a standard Python logging level")
        return normalized

    @field_validator("allowed_source_dialects")
    @classmethod
    def validate_source_dialects(cls, value: str) -> str:
        values = {item.strip().lower() for item in value.split(",") if item.strip()}
        if not values:
            raise ValueError("ALLOWED_SOURCE_DIALECTS must contain at least one dialect")
        unsupported = values - {"postgresql", "sqlserver", "mysql", "oracle"}
        if unsupported:
            raise ValueError(
                "ALLOWED_SOURCE_DIALECTS contains unsupported values: "
                + ", ".join(sorted(unsupported))
            )
        return ",".join(sorted(values))

    @model_validator(mode="after")
    def validate_security_invariants(self) -> Settings:
        if self.embedding_dimensions != REQUIRED_EMBEDDING_DIMENSION:
            raise ValueError(
                "EMBEDDING_DIMENSIONS must be "
                f"{REQUIRED_EMBEDDING_DIMENSION} to match the required schema"
            )

        if not self.celery_task_ignore_result:
            raise ValueError(
                "CELERY_TASK_IGNORE_RESULT must remain true to prevent result persistence"
            )

        if self.app_environment != "test":
            required_secrets = {
                "JWT_SECRET_KEY": self.jwt_secret_key,
                "ENCRYPTION_KEY": self.encryption_key,
                "MINIO_ACCESS_KEY": self.minio_access_key,
                "MINIO_SECRET_KEY": self.minio_secret_key,
            }
            missing = [
                key
                for key, secret in required_secrets.items()
                if not secret or _is_placeholder(secret)
            ]
            if missing:
                raise ValueError(
                    "Non-test configuration requires non-placeholder values for: "
                    + ", ".join(missing)
                )
        return self

    @property
    def source_dialects(self) -> frozenset[str]:
        """Return the configured, normalized source dialect allow-list."""

        return frozenset(self.allowed_source_dialects.split(","))

    @property
    def trusted_host_values(self) -> tuple[str, ...]:
        """Return the configured trusted-host values without wildcard defaults."""

        return tuple(item.strip() for item in self.trusted_hosts.split(",") if item.strip())

    def safe_summary(self) -> dict[str, object]:
        """Expose only non-secret startup diagnostics."""

        return {
            "app_name": self.app_name,
            "environment": self.app_environment,
            "api_prefix": self.api_prefix,
            "allowed_source_dialects": sorted(self.source_dialects),
            "embedding_dimensions": self.embedding_dimensions,
            "query_row_limit": self.source_query_row_limit,
            "query_timeout_seconds": self.source_execution_timeout_seconds,
        }


def _is_placeholder(value: str | SecretStr) -> bool:
    raw_value = value.get_secret_value() if isinstance(value, SecretStr) else value
    lowered = raw_value.strip().lower()
    return not lowered or "replace" in lowered or "change-me" in lowered


@lru_cache
def get_settings() -> Settings:
    """Create a single immutable settings instance per process."""

    return Settings()


def reset_settings_cache() -> None:
    """Test-only helper to reset environment-derived settings."""

    get_settings.cache_clear()
