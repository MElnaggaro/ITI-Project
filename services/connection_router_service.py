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

    def _build_connections_context(self, connections: list[DatabaseConnection]) -> tuple[str, dict[str, UUID]]:
        """Format the connections and their prominent tables for the LLM. Returns string context and mapping."""
        lines = []
        mapping = {}
        for i, conn in enumerate(connections, start=1):
            option_id = str(i)
            mapping[option_id] = conn.id
            tables = list(
                self.db.scalars(
                    select(DatabaseTable.table_name)
                    .where(DatabaseTable.connection_id == conn.id)
                    .where(DatabaseTable.is_enabled == True)
                    .limit(20)
                ).all()
            )
            tables_str = ", ".join(tables) if tables else "No tables or un-synced"
            lines.append(f"Option {option_id}: Name: {conn.name} | Tables: {tables_str}")
            
        return "\n".join(lines), mapping

    def select_best_connection(self, user_message: str, connection_ids: list[UUID]) -> UUID | None:
        """Select the best connection UUID based on the user's message, falling back to active tenant connections if needed."""
        if not connection_ids:
            return None

        # Fetch candidate connections from provided IDs
        connections = list(
            self.db.scalars(
                select(DatabaseConnection)
                .where(DatabaseConnection.id.in_(connection_ids))
            ).all()
        )

        if not connections:
            return connection_ids[0]

        # 1. Fast heuristic keyword match on selected connections
        msg_lower = user_message.lower()
        for conn in connections:
            tables = list(
                self.db.scalars(
                    select(DatabaseTable.table_name)
                    .where(DatabaseTable.connection_id == conn.id)
                    .where(DatabaseTable.is_enabled == True)
                ).all()
            )
            for t in tables:
                t_clean = t.lower()
                stem = t_clean[:-1] if t_clean.endswith("s") and len(t_clean) > 3 else t_clean
                t_space = t_clean.replace("_", " ")
                stem_space = stem.replace("_", " ")
                if stem in msg_lower or t_space in msg_lower or stem_space in msg_lower:
                    logger.info(f"Fast heuristic router matched table '{t}' -> connection '{conn.name}'")
                    return conn.id

        # 2. Fallback heuristic keyword match on ALL active connections in tenant if selected ones don't match
        all_tenant_conns = list(
            self.db.scalars(
                select(DatabaseConnection)
                .where(DatabaseConnection.is_active == True)
            ).all()
        )
        for conn in all_tenant_conns:
            tables = list(
                self.db.scalars(
                    select(DatabaseTable.table_name)
                    .where(DatabaseTable.connection_id == conn.id)
                    .where(DatabaseTable.is_enabled == True)
                ).all()
            )
            for t in tables:
                t_clean = t.lower()
                stem = t_clean[:-1] if t_clean.endswith("s") and len(t_clean) > 3 else t_clean
                t_space = t_clean.replace("_", " ")
                stem_space = stem.replace("_", " ")
                if stem in msg_lower or t_space in msg_lower or stem_space in msg_lower or ("leave" in t_clean and "leave" in msg_lower):
                    logger.info(f"Fallback heuristic router matched table '{t}' -> connection '{conn.name}'")
                    return conn.id


        if len(connection_ids) == 1:
            return connection_ids[0]

        # 3. Fast LLM Routing with qwen3.5:4b
        connections_context, mapping = self._build_connections_context(connections)
        user_prompt = ROUTER_USER_PROMPT_TEMPLATE.format(
            connections_context=connections_context,
            user_message=user_message,
        )


        try:
            raw_output = self.llm_service.chat_completion(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=ROUTER_SYSTEM_PROMPT,
                max_tokens=20,
            )

            
            # Extract Option integer using regex
            match = re.search(r'\b([1-9][0-9]*)\b', raw_output)
            if match:
                selected_option = match.group(1)
                if selected_option in mapping:
                    return mapping[selected_option]
                    
            logger.warning(f"Router LLM returned invalid or unmatched Option: '{raw_output}'. Defaulting to first.")
            return connection_ids[0]
            
        except Exception as e:
            logger.error(f"Failed to route connection via LLM: {e}")
            return connection_ids[0]

