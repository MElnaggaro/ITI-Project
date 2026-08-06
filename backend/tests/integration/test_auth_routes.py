"""Integration tests for authentication API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_auth_full_lifecycle(client: TestClient, db_session: Session):
    """Test full authentication lifecycle: login -> GET /me -> refresh token -> GET /me."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create(name="Acme Corp", code="acme", settings={})
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@acme.com",
        password_hash=hash_password("Secret123!"),
        full_name="Alice Acme",
        is_tenant_admin=True,
    )
    db_session.commit()

    # 1. Login with valid credentials
    login_resp = client.post(
        "/api/auth/login",
        json={"tenant_code": "acme", "email": "user@acme.com", "password": "Secret123!"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 2. Access /api/auth/me with Bearer token
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200, f"GET /me failed: {me_resp.json()}"
    user_info = me_resp.json()
    assert user_info["email"] == "user@acme.com"
    assert user_info["tenant_code"] == "acme"
    assert user_info["tenant_name"] == "Acme Corp"
    assert user_info["is_tenant_admin"] is True

    # 3. Refresh token
    refresh_resp = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_token_data = refresh_resp.json()
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data
    new_access = new_token_data["access_token"]
    new_refresh = new_token_data["refresh_token"]

    # 4. Use new access token on /api/auth/me
    me_resp_2 = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert me_resp_2.status_code == 200
    assert me_resp_2.json()["email"] == "user@acme.com"

    # 5. Reusing rotated old refresh token should be rejected
    reused_resp = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused_resp.status_code == 401


def test_auth_login_failures(client: TestClient, db_session: Session):
    """Test non-enumerating generic 401 failures for bad password or unknown tenant."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create(name="Beta Corp", code="beta")
    user_repo.create(
        tenant_id=tenant.id,
        email="bob@beta.com",
        password_hash=hash_password("BobPass123!"),
    )
    db_session.commit()

    # Wrong password
    resp1 = client.post(
        "/api/auth/login",
        json={"tenant_code": "beta", "email": "bob@beta.com", "password": "WrongPassword!"},
    )
    assert resp1.status_code == 401

    # Unknown tenant code
    resp2 = client.post(
        "/api/auth/login",
        json={"tenant_code": "non-existent", "email": "bob@beta.com", "password": "BobPass123!"},
    )
    assert resp2.status_code == 401

    # Unknown user email
    resp3 = client.post(
        "/api/auth/login",
        json={"tenant_code": "beta", "email": "unknown@beta.com", "password": "BobPass123!"},
    )
    assert resp3.status_code == 401


def test_auth_unauthenticated_me_route(client: TestClient):
    """Test GET /api/auth/me fails when Authorization header is missing or malformed."""
    resp1 = client.get("/api/auth/me")
    assert resp1.status_code == 401

    resp2 = client.get("/api/auth/me", headers={"Authorization": "InvalidHeader"})
    assert resp2.status_code == 401

    resp3 = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_jwt_token"})
    assert resp3.status_code == 401
