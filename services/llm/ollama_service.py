"""Ollama local LLM service for qwen3.5:4b integration across Text-to-SQL and RAG pipelines."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


FAST_MODEL = "qwen2.5:0.5b"


class OllamaLLMService:
    """Service interfacing with local Ollama instance running qwen3.5:4b for enterprise Text-to-SQL & RAG."""

    def __init__(self) -> None:
        settings = get_settings()

        self.provider = settings.llm_provider
        self.model_name = settings.llm_model or "qwen3.5:4b"
        self.base_url = settings.llm_base_url or "http://host.docker.internal:11434"
        self.timeout = max(settings.llm_timeout_seconds, 120)

    def is_enabled(self) -> bool:
        return self.provider == "ollama"

    @staticmethod
    def clean_thinking_tags(text: str) -> str:
        """Strip <think>...</think> reasoning blocks if present."""
        if not text:
            return ""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return cleaned.strip()

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """Call Ollama /api/chat endpoint with safe response parsing and thinking tag cleanup."""
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
                "num_predict": max_tokens,
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

                content = ""
                msg_obj = result.get("message")
                if isinstance(msg_obj, dict):
                    content = msg_obj.get("content", "")

                if not content:
                    choices = result.get("choices")
                    if isinstance(choices, list) and choices:
                        first = choices[0]
                        if isinstance(first, dict):
                            first_msg = first.get("message")
                            if isinstance(first_msg, dict):
                                content = first_msg.get("content", "")

                return self.clean_thinking_tags(str(content))
        except Exception as e:
            logger.error(f"Ollama API call error to {url} (model={self.model_name}): {e}")
            raise RuntimeError(f"LLM Service Offline or Error: {e}")

    def generate_sql(self, schema_context: str, user_prompt: str) -> str:
        """Generate candidate SQL query for given schema context and prompt using qwen3.5:4b with deep reasoning."""
        system_prompt = (
            "You are NEXUS-SQL, an elite Text-to-SQL engineer. Your ONLY job is to output a valid SQL SELECT query.\n\n"
            "## ABSOLUTE RULES (violations are unacceptable):\n"
            "1. Output ONLY the raw SQL SELECT statement. Zero explanations, zero markdown, zero code fences.\n"
            "2. Use ONLY columns and tables explicitly listed in the schema below. NEVER invent or guess table/column names.\n"
            "3. For segment filters like 'VIP', query segment = 'VIP'. Do not invent is_vip or customer_id.\n"
            "4. Keep queries simple and efficient. Avoid unnecessary JOINs or subqueries.\n"
            "5. NEVER use backticks (`). Use standard unquoted identifiers or PostgreSQL double quotes (\") only.\n"
            "6. Default to LIMIT 25 unless the user specifies otherwise.\n"
            "7. If the schema does NOT contain the tables or columns needed to answer the question, output exactly: UNABLE_TO_GENERATE\n"
            "8. Always use ILIKE instead of = for string comparisons in WHERE clauses to ensure case insensitivity.\n"
            "9. NEVER use subqueries like WHERE salary = (SELECT MAX(salary)...). ALWAYS use ORDER BY column DESC LIMIT 1.\n\n"
            "## FEW-SHOT EXAMPLES:\n"
            "User: Who is the highest paid employee and what is their salary?\n"
            "SQL: SELECT first_name, last_name, salary FROM employees ORDER BY salary DESC LIMIT 1\n\n"
            "User: Show me the top 3 most expensive products\n"
            "SQL: SELECT name, price FROM products ORDER BY price DESC LIMIT 3\n\n"
            f"Schema Context:\n{schema_context}\n"
        )

        messages = [{"role": "user", "content": user_prompt}]

        try:
            raw_output = self.chat_completion(messages, system_prompt, max_tokens=1024)

            if "UNABLE_TO_GENERATE" in raw_output.upper():
                raise RuntimeError("LLM could not generate SQL from the provided schema.")

            cleaned_sql = re.sub(r"```(?:sql)?\s*", "", raw_output, flags=re.IGNORECASE)
            cleaned_sql = re.sub(r"```", "", cleaned_sql).replace("`", "").strip()

            if not (cleaned_sql.upper().startswith("SELECT") or cleaned_sql.upper().startswith("WITH")):
                match = re.search(r"\b(SELECT|WITH)\b.*", cleaned_sql, re.IGNORECASE | re.DOTALL)
                if match:
                    cleaned_sql = match.group(0)

            return cleaned_sql
        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            raise RuntimeError(f"LLM SQL Generation Failed: {e}")

    def synthesize_answer(
        self,
        user_message: str,
        intent: str,
        sql_context: str | None = None,
        document_context: str | None = None,
    ) -> str:
        """Synthesize natural language response using qwen3.5:4b with deep reasoning."""
        system_prompt = (
            "You are NEXUS, an enterprise AI assistant. Answer the user question in clear, accurate language matching the user's language (Arabic → Arabic, English → English) using ONLY the provided data.\n\n"
            "## RULES:\n"
            "1. Base answer EXCLUSIVELY on the provided context (SQL results or document excerpts).\n"
            "2. Never guess or infer facts not in the context.\n"
            "3. Start with 💭 **Analysis** (1 line).\n"
            "4. Then give **✅ Answer** using exact numbers/names from context with bullet points.\n"
        )

        context_parts = []
        if sql_context:
            context_parts.append(f"📊 Database Query Results:\n{sql_context}")
        if document_context:
            context_parts.append(f"📄 Document Knowledge Context:\n{document_context}")

        prompt_body = f"User Question: {user_message}\n\n"
        if context_parts:
            prompt_body += "\n\n".join(context_parts) + "\n\n"
        prompt_body += "Provide a well-structured answer following the format rules."

        messages = [{"role": "user", "content": prompt_body}]

        try:
            return self.chat_completion(messages, system_prompt, max_tokens=2048)
        except Exception as e:
            logger.error(f"Failed to synthesize answer: {e}")
            raise RuntimeError(f"LLM Synthesis Failed: {e}")

    def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ):
        """Call Ollama /api/chat with stream=True using qwen3.5:4b and yield JSON chunk objects."""
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        body = {
            "model": self.model_name,
            "messages": payload_messages,
            "stream": True,
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
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
                in_think = False
                for line in resp:
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        msg_obj = chunk.get("message", {})
                        content = msg_obj.get("content", "")

                        if "<think>" in content:
                            in_think = True
                        if "</think>" in content:
                            in_think = False
                            content = content.split("</think>")[-1]

                        if not in_think and content:
                            chunk["message"]["content"] = content
                            yield chunk
        except Exception as e:
            logger.error(f"Ollama API streaming error: {e}")
            raise RuntimeError(f"LLM Service Offline or Error: {e}")

    def stream_synthesize_answer(
        self,
        user_message: str,
        intent: str,
        sql_context: str | None = None,
        document_context: str | None = None,
    ):
        """Synthesize answer and yield text chunks."""
        system_prompt = (
            "You are NEXUS, an enterprise AI assistant. Answer the user question in clear, accurate language matching the user's language (Arabic → Arabic, English → English) using ONLY the provided data.\n\n"
            "## RULES:\n"
            "1. Base answer EXCLUSIVELY on the provided context (SQL results or document excerpts).\n"
            "2. Never guess or infer facts not in the context.\n"
            "3. Start with 💭 **Analysis** (1 line).\n"
            "4. Then give **✅ Answer** using exact numbers/names from context with bullet points.\n"
        )

        context_parts = []
        if sql_context:
            context_parts.append(f"📊 Database Query Results:\n{sql_context}")
        if document_context:
            context_parts.append(f"📄 Document Knowledge Context:\n{document_context}")

        prompt_body = f"User Question: {user_message}\n\n"
        if context_parts:
            prompt_body += "\n\n".join(context_parts) + "\n\n"
        prompt_body += "Provide a well-structured answer following the format rules."

        messages = [{"role": "user", "content": prompt_body}]

        try:
            for chunk in self.stream_chat_completion(messages, system_prompt):
                msg_obj = chunk.get("message", {})
                content = msg_obj.get("content", "")
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Failed to stream synthesize answer: {e}")
            raise RuntimeError(f"LLM Synthesis Failed: {e}")





