"""Security regression tests verifying password, token, connection string, and sensitive column redaction."""

from services.audit_service import redact_sensitive_details
from services.query_execution_service import apply_masking


def test_sensitive_data_redaction_and_column_masking():
    """Verify password, token, connection string, and column values are properly redacted/masked."""
    # 1. Audit redaction test
    audit_data = {
        "user_email": "admin@tenant.com",
        "password": "ClearTextPassword123!",
        "token": "bearer_jwt_token",
        "encrypted_connection_string": "secret_conn_str",
    }

    redacted_audit = redact_sensitive_details(audit_data)

    assert redacted_audit["user_email"] == "admin@tenant.com"
    assert redacted_audit["password"] == "[REDACTED]"
    assert redacted_audit["token"] == "[REDACTED]"
    assert redacted_audit["encrypted_connection_string"] == "[REDACTED]"

    # 2. Sensitive column masking test
    credit_card = "4532-1234-5678-9012"
    assert apply_masking(credit_card, "redact") == "[REDACTED]"
    assert apply_masking(credit_card, "last4") == "***************9012"
    assert len(apply_masking(credit_card, "hash")) == 16
