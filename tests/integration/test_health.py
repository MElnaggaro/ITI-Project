"""Safe foundation health-endpoint tests."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_is_safe_and_returns_request_id() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response.headers
    assert "password" not in response.text.lower()


def test_readiness_does_not_claim_dependency_probes_exist() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["dependencies"] == "deferred_to_owning_phases"
