"""Ollama local LLM service for qwen2.5:0.5b integration across Text-to-SQL and RAG pipelines."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class OllamaLLMService:
    """Service interfacing with local Ollama instance running qwen2.5:0.5b."""

    def __init__(self) -> None:
        settings = get_settings()

        self.provider = settings.llm_provider
        self.model_name = settings.llm_model or "qwen2.5:0.5b"
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
            logger.error(f"Ollama API call error to {url}: {e}")
            raise RuntimeError(f"LLM Service Offline or Error: {e}")


    def generate_sql(self, schema_context: str, user_prompt: str) -> str:
        """Generate candidate SQL query for given schema context and prompt."""
        system_prompt = (
            "You are NEXUS-SQL, an elite Text-to-SQL engineer. Your ONLY job is to output a valid SQL SELECT query.\n\n"
            "## ABSOLUTE RULES (violations are unacceptable):\n"
            "1. Output ONLY the raw SQL SELECT statement. Zero explanations, zero markdown, zero code fences.\n"
            "2. Use ONLY columns and tables explicitly listed in the schema below. Never guess or invent names.\n"
            "3. Keep queries simple and efficient. Avoid unnecessary JOINs or subqueries.\n"
            "4. NEVER use backticks (`). Use standard unquoted identifiers or PostgreSQL double quotes (\") only.\n"
            "5. NEVER use placeholder strings like 'your_code_here' or 'example_value'. Query actual schema columns.\n"
            "6. For listing tables: use 'SELECT table_name FROM database_tables' or 'SELECT table_name FROM information_schema.tables'.\n"
            "7. For active connections: filter by 'is_active = true' or \"status = 'healthy'\".\n"
            "8. Default to LIMIT 25 unless the user specifies otherwise.\n"
            "9. Use COALESCE for nullable columns when presenting results.\n\n"
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
            "You are NEXUS, a world-class Enterprise AI Assistant. You analyze database results and document evidence to deliver clear, actionable answers.\n\n"
            "## THINKING PROCESS (internal, show abbreviated version to user):\n"
            "Before answering, briefly show your reasoning steps:\n"
            "💭 Step 1: Identify what the user is asking\n"
            "💭 Step 2: Locate relevant data from the provided context\n"
            "💭 Step 3: Formulate a precise answer\n\n"
            "## RESPONSE FORMAT RULES:\n"
            "1. Start with a brief 💭 **Analysis** section (2-3 lines max) showing your thinking steps.\n"
            "2. Then provide the **✅ Answer** section with the clear, direct final answer.\n"
            "3. Use **bold** for key facts, numbers, and important terms.\n"
            "4. Use bullet points (•) for listing multiple items. Never use ASCII art tables (+---+, |---|).\n"
            "5. Use numbered lists (1. 2. 3.) for sequential steps.\n"
            "6. Keep paragraphs short (2-3 sentences). Use line breaks between sections.\n"
            "7. For database results: present data as clean bullet points with field labels.\n"
            "8. For document results: always cite [Document Name, Page X].\n"
            "9. Match the user's language (Arabic → Arabic, English → English).\n"
            "10. If no relevant data exists, say so honestly — never fabricate.\n\n"
            "## CRITICAL:\n"
            "- The ✅ Answer must be the MAIN part of your response — detailed, specific, and directly useful.\n"
            "- Never output raw SQL, JSON, or code blocks unless the user explicitly asks for them.\n"
            "- Never start with 'The user query is asking...' or 'Based on the query...'. Be direct.\n"
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
