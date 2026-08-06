import logging
import re
import string
from uuid import UUID

from schemas.chat import IntentType
from services.llm.ollama_service import OllamaLLMService

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM_PROMPT = """You are an intent classifier for an Enterprise AI Assistant.
Your job is to read a user's question and determine the intent based on the available data sources.

Available Data Sources:
- Database Connections (for structured data, tables, analytics, counts, SQL)
- Knowledge Bases (for documents, policies, text, specifications, PDFs)

Available Intents:
- 'database': The question asks for structured data, counts, tables, or analytics (e.g. "How many users?", "List all projects").
- 'document': The question asks for information found in text documents, policies, or specifications (e.g. "What are the core features?", "Summarize the NDA").
- 'hybrid': The question requires cross-referencing BOTH structured database data AND document knowledge (e.g. "Compare our user count in the database with the requirements in the PDF").
- 'general': The question is a simple greeting (e.g. "hi", "hello") or unrelated to the data sources.

RULES:
1. Output exactly ONE word from the intents above. No other text, no explanation.
2. If both Database and Knowledge Base are available, and the question could reasonably apply to both or mentions both, output 'hybrid'.
3. If the user asks about "requirements", "specifications", "features", "goals", this usually implies 'document' or 'hybrid' if comparing to data.
4. If the user asks for "total", "how many", "list all", this usually implies 'database', unless they explicitly ask for a list from a document.
"""

def _fast_greeting_check(user_message: str) -> bool:
    """Quick heuristic to avoid calling LLM for simple greetings."""
    msg_lower = user_message.strip().lower()
    greetings = {
        "hi", "hello", "hey", "howdy", "who are you", "what can you do", "help", "welcome",
        "مرحبا", "ازيك", "السلام عليكم", "مساعدة", "اهلا"
    }
    msg_clean = msg_lower.translate(str.maketrans('', '', string.punctuation)).strip()
    if msg_clean in greetings or any(msg_clean.startswith(g) for g in ["hi ", "hello ", "hey ", "مرحبا ", "ازيك ", "اهلا "]):
        return True
    return False

def classify_request(
    user_message: str,
    database_connection_ids: list[UUID] | None = None,
    knowledge_base_ids: list[UUID] | None = None,
) -> IntentType:
    """Classify user request into one of: general, database, document, hybrid, clarification."""
    if not user_message or len(user_message.strip()) < 2:
        return "clarification"
        
    if _fast_greeting_check(user_message):
        return "general"

    has_conn = bool(database_connection_ids)
    has_kb = bool(knowledge_base_ids)

    # If they didn't select anything, we can't answer data questions
    if not has_conn and not has_kb:
        return "general"

    user_prompt = (
        f"Available Sources:\n"
        f"- Database Selected: {has_conn}\n"
        f"- Knowledge Base Selected: {has_kb}\n\n"
        f"User Question: \"{user_message}\"\n\n"
        f"Intent:"
    )

    try:
        llm = OllamaLLMService()
        if not llm.is_enabled():
            raise RuntimeError("LLM not enabled")
            
        raw_output = llm.chat_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=CLASSIFIER_SYSTEM_PROMPT
        )
        
        # Clean output
        intent = raw_output.strip().lower()
        intent = re.sub(r"[^a-z]", "", intent)
        
        valid_intents: set[IntentType] = {"database", "document", "hybrid", "general", "clarification"}
        if intent in valid_intents:
            # Fallbacks if they chose an intent but the source isn't selected
            if intent == "database" and not has_conn:
                return "clarification"
            if intent == "document" and not has_kb:
                return "clarification"
            if intent == "hybrid":
                if not has_conn: return "document"
                if not has_kb: return "database"
            return intent  # type: ignore
            
    except Exception as e:
        logger.warning(f"LLM classification failed: {e}. Falling back to heuristics.")

    # Fallback if LLM fails
    if has_conn and has_kb:
        return "hybrid"
    elif has_conn:
        return "database"
    elif has_kb:
        return "document"
    
    return "general"
