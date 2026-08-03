"""Message traceability API endpoints for citations and SQL execution details."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from schemas.chat import SourceCitation
from services.citation_service import CitationService

router = APIRouter(prefix="/messages", tags=["Message Traceability"])


@router.get("/{id}/citations", response_model=list[SourceCitation])
def get_message_citations(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> list[SourceCitation]:
    """Get source citations for a specific assistant message."""
    service = CitationService(db)
    return service.get_message_citations(context, id)


@router.get("/{id}/sql", response_model=dict[str, Any])
def get_message_sql(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get generated/normalized SQL execution trace for a database response message."""
    service = CitationService(db)
    sql_trace = service.get_message_sql(context, id)
    if not sql_trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SQL execution trace found for this message.",
        )
    return sql_trace
