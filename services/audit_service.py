"""Audit Service for logging redacted tenant activity and security events."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.audit_log import AuditLog
from repositories.audit_log_repository import AuditLogRepository

REDACTED_KEYS = frozenset(
    {"password", "token", "secret", "connection_string", "encrypted_password", "encrypted_connection_string", "authorization"}
)


def redact_sensitive_details(details: dict[str, Any] | None) -> dict[str, Any]:
    """Recursively redact sensitive key values from audit event details."""
    if not details:
        return {}

    redacted = {}
    for key, value in details.items():
        if key.lower() in REDACTED_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_details(value)
        else:
            redacted[key] = value
    return redacted


class AuditService:
    """Service managing structured tenant audit log creation."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AuditLogRepository(session)

    def log_event(
        self,
        context: TenantContext,
        action: str,
        resource_type: str,
        resource_id: UUID | str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Create a sanitized audit log record."""
        sanitized_details = redact_sensitive_details(details)

        audit_entry = AuditLog(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=UUID(str(resource_id)) if resource_id else None,
            ip_address=ip_address,
            request_id=context.request_id,
            details=sanitized_details,
        )

        return self.repo.create(audit_entry)
