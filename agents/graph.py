"""Single reusable graph boundary; graph construction is implemented in Phase 15."""

from app.exceptions import FeatureNotReadyError


def build_chat_graph() -> None:
    """Refuse to create an ad hoc agent before the approved graph exists."""

    raise FeatureNotReadyError(
        code="chat_graph_not_configured",
        public_message="Chat orchestration is not configured yet.",
        status_code=503,
    )
