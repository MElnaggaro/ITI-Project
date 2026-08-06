"""Celery worker background task definitions for document processing and schema synchronization."""

from uuid import UUID

from workers.celery_app import celery_app


@celery_app.task(name="workers.tasks.process_document_task")
def process_document_task(file_id_str: str, tenant_id_str: str) -> bool:
    """Asynchronously process document parsing, chunking, embedding, and vector store indexing."""
    from app.dependencies import SessionLocal
    from core.tenant_context import TenantContext
    from services.document_pipeline_service import DocumentPipelineService

    file_id = UUID(file_id_str)
    tenant_id = UUID(tenant_id_str)
    context = TenantContext(tenant_id=tenant_id, user_id=tenant_id)

    with SessionLocal() as db:
        pipeline = DocumentPipelineService(db)
        res = pipeline.process_file(context=context, file_id=file_id)
        return res is not None



@celery_app.task(name="workers.tasks.sync_schema_task")
def sync_schema_task(connection_id_str: str, tenant_id_str: str) -> bool:
    """Asynchronously introspect live source database catalog and sync schema metadata."""
    from app.dependencies import SessionLocal
    from core.tenant_context import TenantContext
    from services.schema_sync_service import SchemaSyncService

    conn_id = UUID(connection_id_str)
    tenant_id = UUID(tenant_id_str)
    context = TenantContext(tenant_id=tenant_id, user_id=tenant_id)

    with SessionLocal() as db:
        service = SchemaSyncService(db)
        res = service.sync_schema(context=context, connection_id=conn_id)
        return res is not None

