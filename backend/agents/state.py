"""Typed graph state for ChatOrchestrator pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.tenant_context import TenantContext
from schemas.chat import IntentType
from schemas.knowledge_bases import RetrievedEvidence
from schemas.query_execution import ExecutionResultEnvelope
from schemas.resolved_schema import ResolvedSchema
from schemas.sql_validation import ValidatedQueryPlan


@dataclass(slots=True)
class AgentState:
    """State object passed through the ChatOrchestrator pipeline."""

    context: TenantContext
    conversation_id: UUID
    message_id: UUID
    user_message: str
    database_connection_ids: list[UUID] = field(default_factory=list)
    knowledge_base_ids: list[UUID] = field(default_factory=list)
    detected_intent: IntentType = "general"
    resolved_schema: ResolvedSchema | None = None
    generated_sql: str | None = None
    validated_plan: ValidatedQueryPlan | None = None
    execution_envelope: ExecutionResultEnvelope | None = None
    retrieved_evidence: list[RetrievedEvidence] = field(default_factory=list)
    final_answer: str = ""
    sources_used: list[dict[str, Any]] = field(default_factory=list)
    status: str = "success"
    error_message: str | None = None
