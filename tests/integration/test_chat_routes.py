"""Integration tests for POST /api/chat and POST /api/chat/stream endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable
from models.database_column import DatabaseColumn
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_chat_pipeline_endpoints(client: TestClient, db_session: Session):
    """Test POST /api/chat and POST /api/chat/stream across general and database queries."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Chat Tenant", "chat-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@chat.com",
        password_hash=hash_password("Pass123!"),
    )

    conn = DatabaseConnection(
        id=uuid4(),
        tenant_id=tenant.id,
        name="chat_conn",
        database_type="postgresql",
        status="healthy",
        schema_sync_status="healthy",
        is_active=True,
    )
    s_obj = DatabaseSchema(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_name="public")
    tbl = DatabaseTable(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_id=s_obj.id, table_name="orders", is_enabled=True)
    col = DatabaseColumn(id=uuid4(), tenant_id=tenant.id, table_id=tbl.id, column_name="id", data_type="uuid", is_primary_key=True)

    db_session.add_all([conn, s_obj, tbl, col])
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. General intent chat
    gen_resp = client.post(
        "/api/chat",
        json={"message": "Hello, how can you help me?"},
        headers=headers,
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert gen_data["intent"] == "general"
    assert "AI Assistant" in gen_data["answer"]

    # 2. Database intent chat
    db_resp = client.post(
        "/api/chat",
        json={"message": "SELECT * FROM orders", "database_connection_ids": [str(conn.id)]},
        headers=headers,
    )
    assert db_resp.status_code == 200
    db_data = db_resp.json()
    assert db_data["intent"] in {"database", "hybrid"}

    # 3. Stream chat endpoint
    stream_resp = client.post(
        "/api/chat/stream",
        json={"message": "Hello stream"},
        headers=headers,
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
