"""Conversation management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from schemas.conversations import ConversationCreate, ConversationDetailResponse, ConversationResponse
from services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations Management"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> list[ConversationResponse]:
    """List all tenant conversations."""
    service = ConversationService(db)
    return service.list_conversations(context.tenant_id)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Create a new conversation session."""
    service = ConversationService(db)
    return service.create_conversation(context, data)


@router.get("/{id}", response_model=ConversationDetailResponse)
def get_conversation(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> ConversationDetailResponse:
    """Get detailed conversation metadata and message history."""
    service = ConversationService(db)
    detail = service.get_conversation_detail(context, id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return detail


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_conversation(
    id: UUID,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a conversation and its messages."""
    service = ConversationService(db)
    success = service.delete_conversation(context.tenant_id, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
