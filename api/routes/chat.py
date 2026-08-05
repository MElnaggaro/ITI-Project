"""Chat API endpoints for synchronous and streaming chat orchestration with persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from typing import cast

from agents.graph import ChatOrchestrator
from agents.state import AgentState
from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from models.conversation import Conversation
from models.message import Message
from repositories.conversation_repository import ConversationRepository
from repositories.message_repository import MessageRepository
from schemas.chat import ChatRequest, ChatResponse, Citation, IntentType, SQLDetail
from services.citation_service import CitationService

router = APIRouter(prefix="/chat", tags=["Chat Orchestrator"])


def _get_or_create_conversation(
    db: Session,
    context: TenantContext,
    conv_id: UUID | None,
) -> Conversation:
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


def _execute_chat(
    payload: ChatRequest,
    context: TenantContext,
    db: Session,
) -> ChatResponse:
    """Execute synchronous chat orchestration logic and return ChatResponse envelope."""
    conv = _get_or_create_conversation(db, context, payload.conversation_id)
    user_msg_id = uuid4()
    asst_msg_id = uuid4()

    msg_repo = MessageRepository(db)
    citation_service = CitationService(db)

    # 1. Persist User Prompt Message & Assistant Message Shell
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

    asst_msg = Message(
        id=asst_msg_id,
        tenant_id=context.tenant_id,
        conversation_id=conv.id,
        parent_message_id=user_msg_id,
        role="assistant",
        message_type="text",
        content="",
        status="processing",
    )
    msg_repo.create(asst_msg)

    # 2. Run Chat Pipeline Graph
    state = AgentState(
        context=context,
        conversation_id=conv.id,
        message_id=asst_msg_id,
        user_message=payload.message,
        database_connection_ids=payload.database_connection_ids,
        knowledge_base_ids=payload.knowledge_base_ids,
    )

    orchestrator = ChatOrchestrator(db)
    final_state = orchestrator.run(state)

    # 3. Update Assistant Answer Message
    now = datetime.now(UTC)
    asst_msg.content = final_state.final_answer
    asst_msg.detected_intent = final_state.detected_intent
    asst_msg.selected_sources = final_state.sources_used
    asst_msg.status = "completed"
    db.flush()

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

    # Build Section 9 Contract fields
    sources_used_set = set()
    citations_list: list[Citation] = []

    for src in final_state.sources_used:
        c_type = src.get("citation_type")
        if c_type == "sql":
            sources_used_set.add("database")
            citations_list.append(
                Citation(
                    type="database",
                    table=src.get("table", "unknown"),
                )
            )
        elif c_type == "document":
            sources_used_set.add("documents")
            citations_list.append(
                Citation(
                    type="document",
                    file_name=src.get("file_name", src.get("title", "document")),
                    page=src.get("page_number"),
                )
            )

    sql_detail: SQLDetail | None = None
    if final_state.execution_envelope and final_state.validated_plan:
        sql_detail = SQLDetail(
            query_execution_id=final_state.execution_envelope.execution_id,
            query=final_state.validated_plan.final_sql or final_state.validated_plan.generated_sql,
            row_count=final_state.execution_envelope.returned_row_count,
        )

    return ChatResponse(
        message_id=asst_msg_id,
        conversation_id=conv.id,
        answer=final_state.final_answer,
        intent=cast(IntentType, final_state.detected_intent),
        sources_used=sorted(list(sources_used_set)),
        sql=sql_detail,
        citations=citations_list,
    )


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> ChatResponse | StreamingResponse:
    """Execute synchronous or streaming chat pipeline across SQL and Document RAG engines."""
    if payload.stream:
        return stream_chat(payload, context, db)

    return _execute_chat(payload, context, db)


@router.post("/stream")
def stream_chat(
    payload: ChatRequest,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Execute streaming SSE chat response with Section 9 response contract framing."""
    chat_res = _execute_chat(payload, context, db)

    def _event_generator():
        yield f"data: {json.dumps({'event': 'intent', 'intent': chat_res.intent})}\n\n"
        yield f"data: {json.dumps({'event': 'answer', 'text': chat_res.answer})}\n\n"
        done_payload = json.dumps({"event": "done", "response": chat_res.model_dump(mode="json")})
        yield f"data: {done_payload}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")
