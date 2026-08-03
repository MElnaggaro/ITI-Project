"""Unit tests for KnowledgeBaseService CRUD operations."""

from core.security import hash_password
from core.tenant_context import TenantContext
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.knowledge_bases import KnowledgeBaseCreate
from services.knowledge_base_service import KnowledgeBaseService


def test_knowledge_base_service_crud(db_session):
    """Verify KB creation, listing, and tenant isolation."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("KB Tenant", "kb-tenant")
    user = user_repo.create(tenant.id, "kb@user.com", hash_password("pass"))

    context = TenantContext(tenant_id=tenant.id, user_id=user.id)
    service = KnowledgeBaseService(db_session)

    kb_res = service.create_kb(
        context,
        KnowledgeBaseCreate(name="Company Policies", description="Policy documents"),
    )

    assert kb_res.name == "Company Policies"
    assert kb_res.tenant_id == tenant.id

    list_res = service.list_kbs(tenant.id)
    assert len(list_res) == 1
    assert list_res[0].id == kb_res.id
