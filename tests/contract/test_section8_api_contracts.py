"""Contract verification tests for Section 8 API endpoints and Section 9 chat response envelopes."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_section8_api_contract_responses(client: TestClient, db_session: Session):
    """Verify Section 8 endpoints return required JSON response structures."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Contract Tenant", "contract-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@contract.com",
        password_hash=hash_password("Pass123!"),
    )
    user.is_tenant_admin = True
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/auth/me
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert "id" in me_data
    assert me_data["tenant_id"] == str(tenant.id)

    # 2. GET /api/database-connections
    conn_resp = client.get("/api/database-connections", headers=headers)
    assert conn_resp.status_code == 200
    assert isinstance(conn_resp.json(), list)

    # 3. GET /api/files
    files_resp = client.get("/api/files", headers=headers)
    assert files_resp.status_code == 200
    assert isinstance(files_resp.json(), list)

    # 4. GET /api/knowledge-bases
    kb_resp = client.get("/api/knowledge-bases", headers=headers)
    assert kb_resp.status_code == 200
    assert isinstance(kb_resp.json(), list)

    # 5. GET /api/conversations
    conv_resp = client.get("/api/conversations", headers=headers)
    assert conv_resp.status_code == 200
    assert isinstance(conv_resp.json(), list)

    # 6. POST /api/chat
    chat_resp = client.post("/api/chat", json={"message": "Hello contract"}, headers=headers)
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "message_id" in chat_data
    assert "conversation_id" in chat_data
    assert "answer" in chat_data
    assert "detected_intent" in chat_data
    assert "sources_used" in chat_data

    # 7. GET /api/health
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"
