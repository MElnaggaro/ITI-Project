"""Validation for worker payloads that must not carry secrets or source rows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "credential",
        "connection_string",
        "encrypted_password",
        "source_rows",
        "result_rows",
        "query_result",
        "business_data",
    }
)


@dataclass(frozen=True, slots=True)
class WorkerTaskContext:
    """Only trusted tenant context and resource IDs may cross the worker queue."""

    tenant_id: UUID
    resource_id: UUID
    request_id: str


def validate_worker_payload(payload: Mapping[str, Any]) -> None:
    """Reject nested secret/result payloads before task dispatch."""

    for key, value in payload.items():
        normalized = key.lower()
        if normalized in FORBIDDEN_PAYLOAD_KEYS:
            raise ValueError(f"Worker payload field is forbidden: {key}")
        if isinstance(value, Mapping):
            validate_worker_payload(value)
