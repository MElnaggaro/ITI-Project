"""Knowledge Base management and file association API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from schemas.files import FileAssociateRequest, FileResponse
from schemas.knowledge_bases import KnowledgeBaseCreate, KnowledgeBaseResponse
from services.file_service import FileService
from services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.get("", response_model=list[KnowledgeBaseResponse])
def list_knowledge_bases(
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> list[KnowledgeBaseResponse]:
    """List all tenant knowledge bases."""
    service = KnowledgeBaseService(db)
    return service.list_kbs(context.tenant_id)


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    data: KnowledgeBaseCreate,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> KnowledgeBaseResponse:
    """Create a new tenant knowledge base."""
    service = KnowledgeBaseService(db)
    try:
        return service.create_kb(context, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{id}/files", response_model=FileResponse)
def associate_file_with_knowledge_base(
    id: UUID,
    payload: FileAssociateRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Associate an existing file with a tenant knowledge base."""
    service = FileService(db)
    try:
        return service.associate_file_with_kb(
            tenant_id=context.tenant_id,
            file_id=payload.file_id,
            knowledge_base_id=id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
