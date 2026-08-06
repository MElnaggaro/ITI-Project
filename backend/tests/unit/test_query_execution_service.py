"""Unit tests for QueryExecutionService masking and envelope creation."""

from uuid import uuid4

from services.query_execution_service import apply_masking


def test_apply_masking_policies():
    """Verify redact, last4, and hash masking functions."""
    val = "1234-5678-9012"

    # 1. Redact policy
    assert apply_masking(val, "redact") == "[REDACTED]"

    # 2. Last4 policy
    assert apply_masking(val, "last4") == "**********9012"
    assert apply_masking("123", "last4") == "****"

    # 3. Hash policy
    hashed = apply_masking(val, "hash")
    assert len(hashed) == 16
    assert hashed != val

    # 4. None mask
    assert apply_masking(val, None) == val
