"""File upload and lifecycle management API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from schemas.files import FileResponse
from services.file_service import FileService

router = APIRouter(prefix="/files", tags=["Files Management"])


@router.get("", response_model=list[FileResponse])
def list_files(
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> list[FileResponse]:
    """List all tenant uploaded files."""
    service = FileService(db)
    return service.list_files(context.tenant_id)


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: Annotated[UploadFile, FastAPIFile(...)],
    knowledge_base_id: Annotated[UUID | None, Form()] = None,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Upload a document file (PDF, Word, Excel, CSV, Text)."""
    service = FileService(db)
    try:
        file_bytes = file.file.read()
        return service.upload_file(
            context=context,
            file_bytes=file_bytes,
            filename=file.filename or "uploaded_file",
            content_type=file.content_type,
            knowledge_base_id=knowledge_base_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}", response_model=FileResponse)
def get_file(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Get metadata detail for a specific file."""
    service = FileService(db)
    f_res = service.get_file(context.tenant_id, id)
    if not f_res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return f_res


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_file(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a file and its associated metadata."""
    service = FileService(db)
    success = service.delete_file(context.tenant_id, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/reprocess", response_model=FileResponse)
def reprocess_file(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Reset file processing status to pending for reprocessing."""
    service = FileService(db)
    try:
        return service.reprocess_file(context.tenant_id, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
