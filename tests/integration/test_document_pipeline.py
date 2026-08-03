"""Integration tests for end-to-end DocumentPipelineService (parse -> chunk -> embed -> index)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import hash_password
from core.tenant_context import TenantContext
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from services.document_pipeline_service import DocumentPipelineService
from services.file_service import FileService


def test_document_pipeline_e2e(client: TestClient, db_session: Session):
    """Test full document pipeline from file upload to parsing, chunking, and vector indexing."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Pipe Tenant", "pipe-tenant")
    user = user_repo.create(tenant.id, "pipe@user.com", hash_password("Pass123!"))
    db_session.commit()

    context = TenantContext(tenant_id=tenant.id, user_id=user.id)
    file_service = FileService(db_session)
    pipeline_service = DocumentPipelineService(db_session)

    # 1. Upload sample text file
    file_content = b"Financial report section 1. Sales increased by 20% in Q3. Section 2. Profit margins expanded."
    f_res = file_service.upload_file(
        context=context,
        file_bytes=file_content,
        filename="report.txt",
        content_type="text/plain",
    )

    assert f_res.processing_status == "pending"

    # 2. Process file in document pipeline
    res = pipeline_service.process_file(context, f_res.id)

    assert res["status"] == "completed"
    assert res["chunks_count"] >= 1

    # 3. Verify file record status in database
    updated_f = file_service.get_file(tenant.id, f_res.id)
    assert updated_f.processing_status == "completed"
    assert updated_f.extracted_text_length == len(file_content)
