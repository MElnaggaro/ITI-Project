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
        self.timeout = settings.llm_timeout_seconds or 60

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
            with urllib.request.urlopen(req, timeout=min(self.timeout, 15)) as resp:
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
            logger.warning(f"Ollama API call error to {url}: {e}")
            return ""


    def generate_sql(self, schema_context: str, user_prompt: str) -> str:
        """Generate candidate SQL query for given schema context and prompt."""
        system_prompt = (
            "You are a strict, precise Text-to-SQL engineer. Write a simple, valid SQL SELECT query.\n"
            "Rule 1: Output ONLY the SQL SELECT statement. No explanations, no markdown, no quotes around query.\n"
            "Rule 2: Use ONLY columns and tables explicitly listed in the schema below.\n"
            "Rule 3: Keep queries simple and avoid unnecessary JOINs unless explicitly required by foreign keys.\n"
            "Rule 4: Strictly DO NOT use backticks (`). Use standard unquoted column/table names or PostgreSQL double quotes (\").\n"
            "Rule 5: Strictly DO NOT use placeholder strings like 'your_code_here'. Query actual schema columns directly.\n"
            "Rule 6: For listing tables, do NOT write 'SHOW TABLES'. Use 'SELECT table_name FROM database_tables' or 'SELECT table_name FROM information_schema.tables'.\n"
            "Rule 7: For active database connections, filter by 'is_active = true' or 'status = \'healthy\''.\n\n"
            f"{schema_context}"
        )

        messages = [{"role": "user", "content": user_prompt}]

        try:
            raw_output = self.chat_completion(messages, system_prompt)
            # Clean markdown code blocks and backtick quotes if any returned
            cleaned_sql = re.sub(r"```(?:sql)?\s*", "", raw_output, flags=re.IGNORECASE)
            cleaned_sql = re.sub(r"```", "", cleaned_sql).replace("`", "").strip()
            # Ensure it starts with SELECT or WITH
            if not (cleaned_sql.upper().startswith("SELECT") or cleaned_sql.upper().startswith("WITH")):
                match = re.search(r"\b(SELECT|WITH)\b.*", cleaned_sql, re.IGNORECASE | re.DOTALL)
                if match:
                    cleaned_sql = match.group(0)
            return cleaned_sql
        except Exception as e:
            logger.error(f"Failed to generate SQL with qwen3.5:4b: {e}")
            return ""

    def synthesize_answer(
        self,
        user_message: str,
        intent: str,
        sql_context: str | None = None,
        document_context: str | None = None,
    ) -> str:
        """Synthesize natural language response using qwen3.5:4b."""
        system_prompt = (
            "You are a direct Enterprise AI Assistant.\n"
            "CRITICAL RULES:\n"
            "1. Output ONLY the direct final answer. Absolutely NO preamble, NO 'The user query is asking...', NO step-by-step reasoning.\n"
            "2. State the exact facts directly from the provided Database Query Results and Document Context.\n"
            "3. Do NOT output SQL code blocks or JSON unless asked.\n"
            "4. Match the user's language (Arabic or English).\n"
            "5. Never output raw ASCII box art or borders (e.g., +---+ or |---|). Format all lists and tables cleanly using standard markdown bullet points.\n"
        )

        context_parts = []
        if sql_context:
            context_parts.append(f"Database Query Results:\n{sql_context}")
        if document_context:
            context_parts.append(f"Document Knowledge Context:\n{document_context}")

        prompt_body = f"User Question: {user_message}\n\n"
        if context_parts:
            prompt_body += "\n".join(context_parts) + "\n\n"
        prompt_body += "Please answer the user question based on the provided context."

        messages = [{"role": "user", "content": prompt_body}]

        try:
            return self.chat_completion(messages, system_prompt)
        except Exception as e:
            logger.error(f"Failed to synthesize answer with qwen3.5:4b: {e}")
            return ""
