"""Service to intelligently route user queries to the most relevant database connection."""

from __future__ import annotations

import logging
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.prompts.sql_prompts import ROUTER_SYSTEM_PROMPT, ROUTER_USER_PROMPT_TEMPLATE
from models.database_connection import DatabaseConnection
from models.database_table import DatabaseTable
from services.llm.ollama_service import OllamaLLMService

logger = logging.getLogger(__name__)


class ConnectionRouterService:
    """Uses LLM to route a natural language query to the correct database connection."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.llm_service = OllamaLLMService()

    def _build_connections_context(self, connections: list[DatabaseConnection]) -> str:
        """Format the connections and their prominent tables for the LLM."""
        lines = []
        for conn in connections:
            tables = list(
                self.db.scalars(
                    select(DatabaseTable.table_name)
                    .where(DatabaseTable.connection_id == conn.id)
                    .where(DatabaseTable.is_enabled == True)
                    .limit(20)
                ).all()
            )
            tables_str = ", ".join(tables) if tables else "No tables or un-synced"
            lines.append(f"- ID: {conn.id} | Name: {conn.name} | Tables: {tables_str}")
            
        return "\n".join(lines)

    def select_best_connection(self, user_message: str, connection_ids: list[UUID]) -> UUID | None:
        """Select the best connection UUID based on the user's message."""
        if not connection_ids:
            return None
            
        if len(connection_ids) == 1:
            return connection_ids[0]

        connections = list(
            self.db.scalars(
                select(DatabaseConnection)
                .where(DatabaseConnection.id.in_(connection_ids))
            ).all()
        )
        
        if not connections:
            return connection_ids[0]

        connections_context = self._build_connections_context(connections)
        user_prompt = ROUTER_USER_PROMPT_TEMPLATE.format(
            connections_context=connections_context,
            user_message=user_message,
        )

        try:
            raw_output = self.llm_service.chat_completion(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=ROUTER_SYSTEM_PROMPT
            )
            
            # Extract UUID using regex just in case the LLM outputs extra text
            uuid_pattern = re.compile(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 
                re.IGNORECASE
            )
            match = uuid_pattern.search(raw_output)
            if match:
                selected_uuid = UUID(match.group(0))
                # Verify it's in the allowed list
                if selected_uuid in connection_ids:
                    return selected_uuid
                    
            logger.warning(f"Router LLM returned invalid or unmatched UUID: '{raw_output}'. Defaulting to first.")
            return connection_ids[0]
            
        except Exception as e:
            logger.error(f"Failed to route connection via LLM: {e}")
            return connection_ids[0]
