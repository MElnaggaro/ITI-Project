"""Integration tests for Knowledge Base API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_knowledge_base_routes_lifecycle(client: TestClient, db_session: Session):
    """Test POST /api/knowledge-bases and GET /api/knowledge-bases endpoints."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("KBR Tenant", "kbr-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@kbr.com",
        password_hash=hash_password("Pass123!"),
    )
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Knowledge Base
    create_resp = client.post(
        "/api/knowledge-bases",
        json={"name": "Engineering Docs", "description": "Tech specs"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    kb_data = create_resp.json()
    assert kb_data["name"] == "Engineering Docs"

    # 2. List Knowledge Bases
    list_resp = client.get("/api/knowledge-bases", headers=headers)
    assert list_resp.status_code == 200
    kb_list = list_resp.json()
    assert len(kb_list) == 1
    assert kb_list[0]["name"] == "Engineering Docs"
