"""Unit tests for CitationService message citations and SQL traceability."""

from uuid import uuid4

from core.security import hash_password
from core.tenant_context import TenantContext
from models.query_execution import QueryExecution
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from services.citation_service import CitationService


def test_citation_service_creation_and_traceability(db_session):
    """Verify message citations persistence and SQL trace lookups."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Cit Tenant", "cit-tenant")
    user = user_repo.create(tenant.id, "cit@user.com", hash_password("pass"))
    msg_id = uuid4()
    conn_id = uuid4()

    context = TenantContext(tenant_id=tenant.id, user_id=user.id)
    service = CitationService(db_session)

    # 1. Create message citations
    sources = [
        {"citation_type": "document", "title": "q3_report.pdf", "source_reference": "Page 2", "page_number": 2, "relevance_score": 0.95}
    ]
    created = service.create_citations_for_message(context, msg_id, sources)
    assert len(created) == 1

    # 2. Get message citations
    cits = service.get_message_citations(context, msg_id)
    assert len(cits) == 1
    assert cits[0].title == "q3_report.pdf"

    # 3. Create QueryExecution record for message SQL trace
    q_exec = QueryExecution(
        tenant_id=tenant.id,
        message_id=msg_id,
        connection_id=conn_id,
        generated_sql="SELECT * FROM sales;",
        normalized_sql="SELECT * FROM sales",
        validation_status="valid",
        execution_status="success",
        returned_row_count=10,
    )
    db_session.add(q_exec)
    db_session.commit()

    # 4. Get message SQL trace
    sql_trace = service.get_message_sql(context, msg_id)
    assert sql_trace is not None
    assert sql_trace["generated_sql"] == "SELECT * FROM sales;"
