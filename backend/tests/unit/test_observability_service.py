"""Unit tests for ObservabilityService system health probes."""

from services.observability_service import get_system_health


def test_get_system_health(db_session):
    """Verify health check returns healthy status when database is active."""
    health = get_system_health(db_session)

    assert health["status"] == "healthy"
    assert health["components"]["database"] == "healthy"
