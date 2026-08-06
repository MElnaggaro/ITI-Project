"""Integration tests for POST /api/chat/stream SSE endpoint."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_sse_chat_streaming_flow(client: TestClient, db_session: Session):
    """Test POST /api/chat/stream returns valid Server-Sent Events stream."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("SSE Tenant", "sse-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@sse.com",
        password_hash=hash_password("Pass123!"),
    )
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/chat/stream",
        json={"message": "Hello, explain streaming."},
        headers=headers,
    )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body_text = resp.text

    assert "data: {" in body_text
    assert '"event": "intent"' in body_text
    assert '"event": "done"' in body_text

