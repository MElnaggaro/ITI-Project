"""Structured logging with conservative secret and sensitive-value redaction."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "password",
        "password_hash",
        "secret",
        "token",
        "api_key",
        "connection_string",
        "encrypted_password",
        "encrypted_connection_string",
        "row_filter",
    }
)
REDACTED = "[REDACTED]"


def redact_value(value: Any, key: str | None = None) -> Any:
    """Recursively remove known secret-bearing values from log data."""

    if key and key.lower() in SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, dict):
        return {
            str(item_key): redact_value(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact_value(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    """Minimal dependency-free JSON formatter for safe service logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_value(record.getMessage()),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        extra = getattr(record, "structured", None)
        if extra:
            payload["structured"] = redact_value(extra)
        if record.exc_info:
            payload["exception"] = "exception details withheld from structured logs"
        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    """Configure process logging once without mutating application business state."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
