"""Unit tests for envelope secret encryption and tenant context AAD binding."""

from uuid import uuid4

import pytest

from core.encryption import decrypt_secret, encrypt_secret


def test_encryption_and_decryption_with_matching_tenant():
    """Verify secret encryption and decryption with matching tenant_id."""
    tenant_id = uuid4()
    secret = "SuperSecretDbPassword123!"

    ciphertext = encrypt_secret(secret, tenant_id)
    assert ciphertext is not None
    assert ciphertext != secret

    decrypted = decrypt_secret(ciphertext, tenant_id)
    assert decrypted == secret


def test_decryption_fails_on_tenant_mismatch():
    """Verify decryption fails when supplied with a different tenant_id (AAD binding)."""
    tenant_a = uuid4()
    tenant_b = uuid4()
    secret = "ConfidentialConnectionString"

    ciphertext = encrypt_secret(secret, tenant_a)

    with pytest.raises(ValueError, match="Tenant context mismatch"):
        decrypt_secret(ciphertext, tenant_b)


def test_encryption_none_handling():
    """Verify None inputs return None safely."""
    assert encrypt_secret(None, uuid4()) is None
    assert decrypt_secret(None, uuid4()) is None
