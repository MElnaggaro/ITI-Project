"""Integration tests for health endpoint and audit event logging."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_health_check_endpoint(client: TestClient):
    """Test GET /api/health returns system operational status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["components"]["database"] == "healthy"
