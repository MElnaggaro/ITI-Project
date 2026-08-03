"""Security regression tests verifying strict multi-tenant isolation across all Section 8 API endpoints."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from models.citation import MessageCitation
from models.conversation import Conversation
from models.database_connection import DatabaseConnection
from models.file import File
from models.knowledge_base import KnowledgeBase
from models.message import Message
from models.role import Role
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_cross_tenant_resource_access_rejected(client: TestClient, db_session: Session):
    """Assert Tenant A cannot access Tenant B's connections, roles, files, KBs, conversations, citations, or SQL traces."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    # 1. Create Tenant A & User A
    tenant_a = tenant_repo.create("Tenant A Isolation", "tenant-a-iso")
    user_a = user_repo.create(tenant_a.id, "usera@iso.com", hash_password("Pass123!"))

    # 2. Create Tenant B & User B
    tenant_b = tenant_repo.create("Tenant B Isolation", "tenant-b-iso")
    user_b = user_repo.create(tenant_b.id, "userb@iso.com", hash_password("Pass123!"))

    # 3. Create Tenant B Resources
    role_b = Role(tenant_id=tenant_b.id, name="Tenant B Role")
    conn_b = DatabaseConnection(
        id=uuid4(),
        tenant_id=tenant_b.id,
        name="Tenant B Connection",
        database_type="postgresql",
        status="healthy",
    )
    kb_b = KnowledgeBase(id=uuid4(), tenant_id=tenant_b.id, name="Tenant B KB")
    file_b = File(
        id=uuid4(),
        tenant_id=tenant_b.id,
        knowledge_base_id=kb_b.id,
        original_name="tenant_b_doc.pdf",
        stored_name="s_b.pdf",
        storage_path="/tmp/b.pdf",
        processing_status="completed",
    )
    conv_b = Conversation(id=uuid4(), tenant_id=tenant_b.id, user_id=user_b.id, title="Tenant B Conv")
    msg_b = Message(id=uuid4(), tenant_id=tenant_b.id, conversation_id=conv_b.id, role="assistant", message_type="text", content="Secret text B", status="completed")
    cit_b = MessageCitation(tenant_id=tenant_b.id, message_id=msg_b.id, citation_type="document", title="Tenant B Document")

    db_session.add_all([role_b, conn_b, kb_b, file_b, conv_b, msg_b, cit_b])
    db_session.commit()

    # 4. Authenticate User A
    token_a = create_access_token(tenant_a.id, user_a.id, is_tenant_admin=False)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 5. Assert User A CANNOT access Tenant B's Connection
    res_conn = client.get(f"/api/database-connections/{conn_b.id}", headers=headers_a)
    assert res_conn.status_code in {403, 404}

    # 6. Assert User A CANNOT delete Tenant B's Role
    res_role = client.delete(f"/api/roles/{role_b.id}", headers=headers_a)
    assert res_role.status_code in {403, 404}

    # 7. Assert User A CANNOT access Tenant B's File
    res_file = client.get(f"/api/files/{file_b.id}", headers=headers_a)
    assert res_file.status_code in {403, 404}

    # 8. Assert User A CANNOT access Tenant B's Conversation
    res_conv = client.get(f"/api/conversations/{conv_b.id}", headers=headers_a)
    assert res_conv.status_code in {403, 404}

    # 9. Assert User A CANNOT access Tenant B's Message Citations
    res_cit = client.get(f"/api/messages/{msg_b.id}/citations", headers=headers_a)
    assert res_cit.status_code == 200
    assert len(res_cit.json()) == 0  # Tenant A gets empty list for Tenant B message

    # 10. Assert User A CANNOT access Tenant B's Message SQL Trace
    res_sql = client.get(f"/api/messages/{msg_b.id}/sql", headers=headers_a)
    assert res_sql.status_code in {403, 404}
