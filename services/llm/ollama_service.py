"""Ollama local LLM service for qwen3.5:4b integration across Text-to-SQL and RAG pipelines."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class OllamaLLMService:
    """Service interfacing with local Ollama instance running qwen3.5:4b."""

    def __init__(self) -> None:
        settings = get_settings()

        self.provider = settings.llm_provider
        self.model_name = settings.llm_model or "qwen3.5:4b"
        self.base_url = settings.llm_base_url or "http://host.docker.internal:11434"
        self.timeout = settings.llm_timeout_seconds

    def is_enabled(self) -> bool:
        return self.provider == "ollama"

    def chat_completion(self, messages: list[dict[str, str]], system_prompt: str | None = None) -> str:
        """Call Ollama /api/chat or /v1/chat/completions endpoint with safe response parsing."""
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        body = {
            "model": self.model_name,
            "messages": payload_messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))

                # 1. Check Native Ollama format: {"message": {"content": "..."}}
                msg_obj = result.get("message")
                if isinstance(msg_obj, dict):
                    content = msg_obj.get("content")
                    if content:
                        return str(content).strip()

                # 2. Check OpenAI format: {"choices": [{"message": {"content": "..."}}]}
                choices = result.get("choices")
                if isinstance(choices, list) and choices:
                    first = choices[0]
                    if isinstance(first, dict):
                        first_msg = first.get("message")
                        if isinstance(first_msg, dict):
                            content = first_msg.get("content")
                            if content:
                                return str(content).strip()

                return ""
        except Exception as e:
            logger.error(f"Ollama API call error to {url}: {e}")
            raise RuntimeError(f"LLM Service Offline or Error: {e}")


    def generate_sql(self, schema_context: str, user_prompt: str) -> str:
        """Generate candidate SQL query for given schema context and prompt."""
        system_prompt = (
            "You are NEXUS-SQL, an elite Text-to-SQL engineer. Your ONLY job is to output a valid SQL SELECT query.\n\n"
            "## ABSOLUTE RULES (violations are unacceptable):\n"
            "1. Output ONLY the raw SQL SELECT statement. Zero explanations, zero markdown, zero code fences.\n"
            "2. Use ONLY columns and tables explicitly listed in the schema below. NEVER invent or guess table/column names.\n"
            "3. Keep queries simple and efficient. Avoid unnecessary JOINs or subqueries.\n"
            "4. NEVER use backticks (`). Use standard unquoted identifiers or PostgreSQL double quotes (\") only.\n"
            "5. NEVER use placeholder strings like 'your_code_here' or 'example_value'. Query actual schema columns.\n"
            "6. Default to LIMIT 25 unless the user specifies otherwise.\n"
            "7. Use COALESCE for nullable columns when presenting results.\n"
            "8. If the schema does NOT contain the tables or columns needed to answer the question, output exactly: UNABLE_TO_GENERATE\n"
            "9. Always use ILIKE instead of = for string comparisons in WHERE clauses to ensure case insensitivity.\n\n"
            "## FEW-SHOT EXAMPLES:\n"
            "User: How many users are in the system?\n"
            "SQL: SELECT COUNT(*) AS user_count FROM users\n\n"
            "User: List all files with their processing status\n"
            "SQL: SELECT original_name, processing_status FROM files\n\n"
            "User: Show me active database connections\n"
            "SQL: SELECT name, database_type, host, status FROM database_connections WHERE is_active = true\n\n"
            "User: How many tables are in the database?\n"
            "SQL: SELECT COUNT(*) AS table_count FROM database_tables\n\n"
            "User: Which tables have the most columns?\n"
            "SQL: SELECT dt.table_name, COUNT(dc.id) AS column_count FROM database_tables dt JOIN database_columns dc ON dt.id = dc.table_id GROUP BY dt.table_name ORDER BY column_count DESC LIMIT 10\n\n"
            "User: Count the total number of columns across all tables\n"
            "SQL: SELECT COUNT(*) AS total_columns FROM database_columns\n\n"
            "User: Show me all roles and how many users are assigned to each\n"
            "SQL: SELECT r.name, COUNT(ur.user_id) AS user_count FROM roles r LEFT JOIN user_roles ur ON r.id = ur.role_id GROUP BY r.id, r.name\n\n"
            "User: What is the total file size of all uploaded documents?\n"
            "SQL: SELECT SUM(file_size_bytes) AS total_size_bytes FROM files\n\n"
            f"\n{schema_context}"
        )

        messages = [{"role": "user", "content": user_prompt}]

        try:
            raw_output = self.chat_completion(messages, system_prompt)

            # Check if the model explicitly said it can't generate
            if "UNABLE_TO_GENERATE" in raw_output.upper():
                raise RuntimeError("LLM could not generate SQL from the provided schema.")

            # Clean markdown code blocks and backtick quotes if any returned
            cleaned_sql = re.sub(r"```(?:sql)?\s*", "", raw_output, flags=re.IGNORECASE)
            cleaned_sql = re.sub(r"```", "", cleaned_sql).replace("`", "").strip()

            # Extract just the SQL statement if there's extra text
            if not (cleaned_sql.upper().startswith("SELECT") or cleaned_sql.upper().startswith("WITH")):
                match = re.search(r"\b(SELECT|WITH)\b.*", cleaned_sql, re.IGNORECASE | re.DOTALL)
                if match:
                    cleaned_sql = match.group(0)

            # Post-generation validation: check that referenced tables exist in schema
            schema_tables = set(re.findall(r"Table\s+'(?:\w+\.)?(\w+)'", schema_context, re.IGNORECASE))
            # Also add information_schema tables as valid
            schema_tables.update({"information_schema", "pg_catalog"})
            if schema_tables:
                sql_tables = set(re.findall(r"\bFROM\s+(?:public\.)?(\w+)|\bJOIN\s+(?:public\.)?(\w+)", cleaned_sql, re.IGNORECASE))
                sql_table_names = {t for group in sql_tables for t in group if t}
                invalid_tables = sql_table_names - schema_tables
                if invalid_tables:
                    logger.warning(f"SQL references non-existent tables: {invalid_tables}. Available: {schema_tables}")

            return cleaned_sql
        except Exception as e:
            logger.error(f"Failed to generate SQL with {self.model_name}: {e}")
            raise RuntimeError(f"LLM SQL Generation Failed: {e}")

    def synthesize_answer(
        self,
        user_message: str,
        intent: str,
        sql_context: str | None = None,
        document_context: str | None = None,
    ) -> str:
        """Synthesize natural language response using the configured LLM model."""
        system_prompt = (
            "You are NEXUS, an Enterprise AI Assistant. Your job is to answer the user's question using ONLY the data provided below.\n\n"
            "## CRITICAL GROUNDING RULES (NEVER VIOLATE):\n"
            "1. Your answer MUST be based EXCLUSIVELY on the provided context data (SQL results or document excerpts).\n"
            "2. NEVER make up, guess, or infer numbers, names, dates, or facts that are not explicitly in the context.\n"
            "3. If SQL query results show a count of 1, say '1'. If results show 3 rows, describe those 3 rows. Use the EXACT data.\n"
            "4. If document excerpts mention specific values (e.g., '20 days PTO', 'AES-256'), use those EXACT values.\n"
            "5. If the provided context does not contain enough information, say 'The available data does not contain this information.'\n"
            "6. NEVER use your general knowledge to supplement or override the provided context data.\n\n"
            "## RESPONSE FORMAT:\n"
            "1. Start with a brief 💭 **Analysis** (1-2 lines: what data source you used and what you found).\n"
            "2. Then give the **✅ Answer** with the direct, specific answer using the exact data from the context.\n"
            "3. Use **bold** for key numbers and facts.\n"
            "4. Use bullet points (•) for listing items.\n"
            "5. For document answers: cite [Document Name, Page X].\n"
            "6. Match the user's language (Arabic → Arabic, English → English).\n"
            "7. Keep the answer concise and focused. Do not ramble or pad with generic information.\n"
            "8. Never output raw SQL, JSON, or code blocks unless asked.\n"
        )

        context_parts = []
        if sql_context:
            context_parts.append(f"📊 Database Query Results:\n{sql_context}")
        if document_context:
            context_parts.append(f"📄 Document Knowledge Context:\n{document_context}")

        prompt_body = f"User Question: {user_message}\n\n"
        if context_parts:
            prompt_body += "\n\n".join(context_parts) + "\n\n"
        prompt_body += "Analyze the above context and provide a well-structured answer following the format rules."

        messages = [{"role": "user", "content": prompt_body}]

        try:
            return self.chat_completion(messages, system_prompt)
        except Exception as e:
            logger.error(f"Failed to synthesize answer with {self.model_name}: {e}")
            raise RuntimeError(f"LLM Synthesis Failed: {e}")
