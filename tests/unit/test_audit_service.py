"""Unit tests for AuditService event logging and sensitive data redaction."""

from uuid import uuid4

from core.tenant_context import TenantContext
from services.audit_service import AuditService, redact_sensitive_details


def test_redact_sensitive_details():
    """Verify sensitive keys like password and token are redacted."""
    details = {
        "username": "admin",
        "password": "SecretPassword123!",
        "token": "bearer_jwt_token_value",
        "connection_string": "postgresql://user:pass@localhost:5432/db",
        "nested": {"secret": "my_secret_key", "public": "safe_value"},
    }

    sanitized = redact_sensitive_details(details)

    assert sanitized["username"] == "admin"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["connection_string"] == "[REDACTED]"
    assert sanitized["nested"]["secret"] == "[REDACTED]"
    assert sanitized["nested"]["public"] == "safe_value"


def test_audit_service_log_event(db_session):
    """Verify AuditService persists sanitized audit entry in database."""
    tenant_id = uuid4()
    user_id = uuid4()
    context = TenantContext(tenant_id=tenant_id, user_id=user_id, request_id="req_12345")

    service = AuditService(db_session)
    entry = service.log_event(
        context=context,
        action="user_login",
        resource_type="user",
        resource_id=user_id,
        details={"email": "user@test.com", "password": "SuperSecretPassword!"},
    )

    assert entry.tenant_id == tenant_id
    assert entry.action == "user_login"
    assert entry.details["password"] == "[REDACTED]"
    assert entry.request_id == "req_12345"
