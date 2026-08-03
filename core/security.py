"""Security helper boundary; JWT and Argon2id behavior is implemented in Phase 03."""

from app.exceptions import FeatureNotReadyError


def authentication_not_ready() -> None:
    """Prevent callers from treating a Phase 01 placeholder as real auth."""

    raise FeatureNotReadyError(
        code="authentication_not_configured",
        public_message="Authentication is not configured yet.",
        status_code=503,
    )
