"""Integration tests for message citations and SQL traceability endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from models.citation import MessageCitation
from models.conversation import Conversation
from models.message import Message
from models.query_execution import QueryExecution
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_message_traceability_routes(client: TestClient, db_session: Session):
    """Test GET /api/messages/{id}/citations and GET /api/messages/{id}/sql endpoints."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("MR Tenant", "mr-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@mr.com",
        password_hash=hash_password("Pass123!"),
    )

    conv = Conversation(id=uuid4(), tenant_id=tenant.id, user_id=user.id, title="Test Trace")
    asst_msg = Message(id=uuid4(), tenant_id=tenant.id, conversation_id=conv.id, role="assistant", message_type="text", content="Answer text", status="completed")
    cit = MessageCitation(tenant_id=tenant.id, message_id=asst_msg.id, citation_type="document", title="policy.pdf", source_reference="Page 1", relevance_score=0.9)
    q_exec = QueryExecution(tenant_id=tenant.id, message_id=asst_msg.id, connection_id=uuid4(), generated_sql="SELECT 1;", validation_status="valid", execution_status="success")

    db_session.add_all([conv, asst_msg, cit, q_exec])
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get message citations
    cits_resp = client.get(f"/api/messages/{asst_msg.id}/citations", headers=headers)
    assert cits_resp.status_code == 200
    cits_data = cits_resp.json()
    assert len(cits_data) == 1
    assert cits_data[0]["title"] == "policy.pdf"

    # 2. Get message SQL trace
    sql_resp = client.get(f"/api/messages/{asst_msg.id}/sql", headers=headers)
    assert sql_resp.status_code == 200
    sql_data = sql_resp.json()
    assert sql_data["generated_sql"] == "SELECT 1;"
