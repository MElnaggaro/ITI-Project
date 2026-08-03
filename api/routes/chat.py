"""Chat API endpoints for synchronous and streaming chat orchestration with persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from agents.graph import ChatOrchestrator
from agents.state import AgentState
from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from models.conversation import Conversation
from models.message import Message
from repositories.conversation_repository import ConversationRepository
from repositories.message_repository import MessageRepository
from schemas.chat import ChatRequest, ChatResponse, SourceCitation
from services.citation_service import CitationService

router = APIRouter(prefix="/chat", tags=["Chat Orchestrator"])


def _get_or_create_conversation(db: Session, context: TenantContext, conv_id: UUID | None) -> Conversation:
    conv_repo = ConversationRepository(db)
    if conv_id:
        existing = conv_repo.get_by_id(context.tenant_id, conv_id)
        if existing:
            return existing

    new_conv = Conversation(
        id=conv_id or uuid4(),
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        title="Chat Conversation",
        status="active",
    )
    return conv_repo.create(new_conv)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Execute synchronous chat pipeline across SQL and Document RAG engines."""
    conv = _get_or_create_conversation(db, context, payload.conversation_id)
    user_msg_id = uuid4()
    asst_msg_id = uuid4()

    msg_repo = MessageRepository(db)
    citation_service = CitationService(db)

    # 1. Persist User Prompt Message
    user_msg = Message(
        id=user_msg_id,
        tenant_id=context.tenant_id,
        conversation_id=conv.id,
        role="user",
        message_type="text",
        content=payload.message,
        status="completed",
    )
    msg_repo.create(user_msg)

    # 2. Run Chat Pipeline Graph
    state = AgentState(
        context=context,
        conversation_id=conv.id,
        message_id=asst_msg_id,
        user_message=payload.message,
        connection_ids=payload.connection_ids,
        knowledge_base_ids=payload.knowledge_base_ids,
    )

    orchestrator = ChatOrchestrator(db)
    final_state = orchestrator.run(state)

    # 3. Persist Assistant Answer Message
    now = datetime.now(timezone.utc)
    asst_msg = Message(
        id=asst_msg_id,
        tenant_id=context.tenant_id,
        conversation_id=conv.id,
        parent_message_id=user_msg_id,
        role="assistant",
        message_type="text",
        content=final_state.final_answer,
        detected_intent=final_state.detected_intent,
        selected_sources=final_state.sources_used,
        status="completed",
    )
    msg_repo.create(asst_msg)

    # 4. Update Conversation Timestamps
    conv.last_message_at = now
    conv.updated_at = now
    db.flush()

    # 5. Persist Message Citations
    if final_state.sources_used:
        citation_service.create_citations_for_message(
            context=context,
            message_id=asst_msg_id,
            sources=final_state.sources_used,
        )

    sources = [
        SourceCitation(
            citation_type=src.get("citation_type", "general"),
            title=src.get("title", "Source"),
            source_reference=src.get("source_reference", ""),
            page_number=src.get("page_number"),
            relevance_score=src.get("relevance_score"),
        )
        for src in final_state.sources_used
    ]

    gen_sql = final_state.validated_plan.final_sql if final_state.validated_plan else None
    exec_time = final_state.execution_envelope.execution_time_ms if final_state.execution_envelope else None
    r_count = final_state.execution_envelope.returned_row_count if final_state.execution_envelope else None

    return ChatResponse(
        message_id=asst_msg_id,
        conversation_id=conv.id,
        answer=final_state.final_answer,
        detected_intent=final_state.detected_intent,
        sources_used=sources,
        generated_sql=gen_sql,
        execution_time_ms=exec_time,
        row_count=r_count,
    )


@router.post("/stream")
def stream_chat(
    payload: ChatRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Execute streaming SSE chat response with Section 9 response contract framing."""
    chat_res = chat(payload, context, db)

    def _event_generator():
        yield f"data: {json.dumps({'event': 'intent', 'intent': chat_res.detected_intent})}\n\n"
        yield f"data: {json.dumps({'event': 'answer', 'text': chat_res.answer})}\n\n"
        yield f"data: {json.dumps({'event': 'done', 'response': chat_res.model_dump(mode='json')})}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")
