"""Connection-secret encryption module using Fernet symmetric encryption with tenant AAD context binding."""

from __future__ import annotations

import base64
import json
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings

_SALT = b"platform_connection_encryption_salt_v1"


def _get_fernet_key() -> bytes:
    settings = get_settings()
    raw_key = None
    if settings.encryption_key:
        raw_key = settings.encryption_key.get_secret_value()
    elif settings.app_environment == "test":
        raw_key = "test-encryption-key-for-unit-and-integration-tests"

    if not raw_key:
        raise ValueError("ENCRYPTION_KEY must be configured in non-test environment")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=100_000,
    )
    key_bytes = kdf.derive(raw_key.encode("utf-8"))
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_secret(secret_text: str | None, tenant_id: UUID | str) -> str | None:
    """Encrypt plaintext string bound to trusted tenant_id context."""
    if secret_text is None:
        return None

    fernet = Fernet(_get_fernet_key())
    payload = json.dumps({"t": str(tenant_id), "s": secret_text})
    ciphertext = fernet.encrypt(payload.encode("utf-8"))
    return ciphertext.decode("utf-8")


def decrypt_secret(ciphertext: str | None, tenant_id: UUID | str) -> str | None:
    """Decrypt ciphertext and verify tenant_id context binding."""
    if ciphertext is None:
        return None

    fernet = Fernet(_get_fernet_key())
    try:
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
        data = json.loads(decrypted.decode("utf-8"))
    except (InvalidToken, Exception) as exc:
        raise ValueError(f"Secret decryption failed: {exc}")

    if data.get("t") != str(tenant_id):
        raise ValueError("Tenant context mismatch during secret decryption.")

    return data.get("s")
