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
                prompt = (
                    "Rephrase the following user search query into 1-2 concise, keyphrase-dense sentences "
                    f"optimized for vector search retrieval in a technical knowledge base. Query: '{clean_query}'"
                )
                rewritten = ollama_svc.synthesize_answer(user_message=prompt, intent="document")
                if rewritten and len(rewritten) > 5:
                    return rewritten.strip()
        except Exception:
            pass

        # 2. Heuristic query expansion fallback
        words = clean_query.split()
        if len(words) <= 3:
            return f"{clean_query} details specifications summary overview"
        return clean_query
