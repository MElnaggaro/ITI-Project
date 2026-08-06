"""Query Rewriter service for expanding user RAG queries into optimized retrieval search terms."""

from __future__ import annotations


class QueryRewriterService:
    """Expands natural language user queries for vector similarity retrieval."""

    def rewrite_query(self, user_query: str, conversation_context: str | None = None) -> str:
        """Rewrite and optimize user query for document chunk retrieval."""
        clean_query = user_query.strip()
        if not clean_query:
            return ""

        # 1. Try Ollama LLM query rewriting if enabled
        try:
            from services.llm.ollama_service import OllamaLLMService

            ollama_svc = OllamaLLMService()
            if ollama_svc.is_enabled():
                system_prompt = (
                    "You are a search query optimizer. Your job is to extract the most important keywords "
                    "from the user's question to be used in a vector search. Output ONLY space-separated keywords. "
                    "No conversational text, no formatting."
                )
                messages = [{"role": "user", "content": f"Query: '{clean_query}'"}]
                rewritten = ollama_svc.chat_completion(messages=messages, system_prompt=system_prompt)
                
                if rewritten and len(rewritten) > 2:
                    return rewritten.strip()
        except Exception:
            pass

        # 2. Heuristic query expansion fallback
        words = clean_query.split()
        if len(words) <= 3:
            return f"{clean_query} details specifications summary overview"
        return clean_query
