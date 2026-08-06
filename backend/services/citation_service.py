"""Citation Service managing citation persistence and message SQL traceability lookups."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.citation import MessageCitation
from models.message import Message
from models.query_execution import QueryExecution
from repositories.citation_repository import CitationRepository
from schemas.chat import SourceCitation


class CitationService:
    """Service managing message citations and traceability lookups."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = CitationRepository(session)

    def create_citations_for_message(
        self,
        context: TenantContext,
        message_id: UUID,
        sources: list[dict[str, Any]],
    ) -> list[MessageCitation]:
        """Persist citation records for an assistant response message."""
        citations = []
        for src in sources:
            cit = MessageCitation(
                tenant_id=context.tenant_id,
                message_id=message_id,
                citation_type=src.get("citation_type", "document"),
                file_id=src.get("file_id"),
                chunk_id=src.get("chunk_id"),
                query_execution_id=src.get("query_execution_id"),
                title=src.get("title", "Source"),
                source_reference=src.get("source_reference", ""),
                page_number=src.get("page_number"),
                relevance_score=src.get("relevance_score"),
            )
            created = self.repo.create(cit)
            citations.append(created)

        return citations

    def get_message_citations(
        self,
        context: TenantContext,
        message_id: UUID,
    ) -> list[SourceCitation]:
        """Fetch citations for a specific message."""
        cits = self.repo.list_by_message(context.tenant_id, message_id)
        return [
            SourceCitation(
                citation_type=c.citation_type,
                title=c.title,
                source_reference=c.source_reference,
                page_number=c.page_number,
                relevance_score=c.relevance_score,
            )
            for c in cits
        ]

    def get_message_sql(
        self,
        context: TenantContext,
        message_id: UUID,
    ) -> dict[str, Any] | None:
        """Fetch query execution trace for a database response message."""
        q_exec = self.session.scalar(
            select(QueryExecution)
            .where(QueryExecution.tenant_id == context.tenant_id)
            .where(QueryExecution.message_id == message_id)
        )
        if not q_exec:
            return None

        return {
            "message_id": str(message_id),
            "execution_id": str(q_exec.id),
            "generated_sql": q_exec.generated_sql,
            "normalized_sql": q_exec.normalized_sql,
            "validation_status": q_exec.validation_status,
            "execution_status": q_exec.execution_status,
            "execution_time_ms": q_exec.execution_time_ms,
            "returned_row_count": q_exec.returned_row_count,
        }
