"""Integration tests for conversation CRUD endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_conversation_routes_lifecycle(client: TestClient, db_session: Session):
    """Test POST /api/conversations, GET /api/conversations, GET /api/conversations/{id}, DELETE /api/conversations/{id}."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("CR Tenant", "cr-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@cr.com",
        password_hash=hash_password("Pass123!"),
    )
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create conversation
    create_resp = client.post(
        "/api/conversations",
        json={"title": "Q3 Sales Q&A"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    conv_data = create_resp.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Q3 Sales Q&A"

    # 2. List conversations
    list_resp = client.get("/api/conversations", headers=headers)
    assert list_resp.status_code == 200
    conv_list = list_resp.json()
    assert len(conv_list) == 1

    # 3. Get conversation detail
    detail_resp = client.get(f"/api/conversations/{conv_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == conv_id

    # 4. Delete conversation
    del_resp = client.delete(f"/api/conversations/{conv_id}", headers=headers)
    assert del_resp.status_code == 204
