"""Unit tests for ConversationService CRUD operations."""

from core.security import hash_password
from core.tenant_context import TenantContext
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.conversations import ConversationCreate
from services.conversation_service import ConversationService


def test_conversation_service_crud(db_session):
    """Verify conversation creation, listing, detail retrieval, and deletion."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Conv Tenant", "conv-tenant")
    user = user_repo.create(tenant.id, "conv@user.com", hash_password("pass"))

    context = TenantContext(tenant_id=tenant.id, user_id=user.id)
    service = ConversationService(db_session)

    c_res = service.create_conversation(context, ConversationCreate(title="Sales Analysis"))

    assert c_res.title == "Sales Analysis"
    assert c_res.tenant_id == tenant.id

    list_res = service.list_conversations(tenant.id)
    assert len(list_res) == 1
    assert list_res[0].id == c_res.id

    detail = service.get_conversation_detail(context, c_res.id)
    assert detail is not None
    assert detail.id == c_res.id

    deleted = service.delete_conversation(tenant.id, c_res.id)
    assert deleted is True
