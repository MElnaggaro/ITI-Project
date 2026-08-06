"""Authorization primitive boundary; permission evaluation is implemented in Phase 04."""

from app.exceptions import FeatureNotReadyError


def authorization_not_ready() -> None:
    """Fail closed rather than allowing access before authorization exists."""

    raise FeatureNotReadyError(
        code="authorization_not_configured",
        public_message="Authorization is not configured yet.",
        status_code=503,
    )
