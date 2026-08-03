"""Connection-secret encryption boundary; implementation is owned by Phase 05."""

from app.exceptions import FeatureNotReadyError


def encryption_not_ready() -> None:
    """Prevent plaintext fallback before the encryption service exists."""

    raise FeatureNotReadyError(
        code="encryption_not_configured",
        public_message="Connection secret handling is not configured yet.",
        status_code=503,
    )
