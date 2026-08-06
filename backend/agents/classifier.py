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
- 'database': The question asks for structured data, counts, tables, or analytics (e.g. "How many users?", "List all projects", "Top 3 products").
- 'document': The question asks for information found in text documents, policies, or specifications (e.g. "What is the PTO policy?", "Password requirements").
- 'hybrid': The question EXPLICITLY asks to compare or cross-reference BOTH structured database data AND document knowledge (e.g. "Compare our user count in the database with the requirements in the PDF").
- 'general': The question is a simple greeting (e.g. "hi", "hello") or unrelated to the data sources.

CRITICAL CLASSIFICATION RULES:
1. Output exactly ONE word from the intents above. No other text, no explanation.
2. Questions asking "how many", "count", "list", "top N", "orders", "customers", "products", "salaries", "budget" MUST be classified as 'database' unless comparing with a PDF.
3. Questions asking about "policy", "handbook", "PTO", "vacation", "rules", "specifications", "encryption", "requirements" MUST be classified as 'document' unless comparing with SQL data.
4. ONLY output 'hybrid' if the user question explicitly asks to compare, reconcile, or cross-reference data from BOTH sources.
"""

HYBRID_TRIGGER_KEYWORDS = {
    "compare", "versus", "vs", "reconcile", "cross-reference", "both sources",
    "database and document", "pdf and database", "contract vs invoice",
    "قارن", "مقارنة", "مطابقة"
}

DOCUMENT_TRIGGER_KEYWORDS = {
    "policy", "pto", "vacation", "leave policy", "sick leave", "sick", "entitled", "entitlement",
    "allowance", "benefits", "rules", "handbook", "nda", "sla", "specification", "specifications",
    "encryption standard", "password requirement", "security policy", "ci/cd", "pipeline",
    "architecture", "doc", "document", "pdf", "سياسة", "اجازات", "مرضي", "شروط", "ملف", "وثيقة"
}


DATABASE_TRIGGER_KEYWORDS = {
    "how many", "count", "list all", "total", "top 3", "top 5", "most expensive",
    "highest paid", "cheapest", "registered", "customers", "orders", "products",
    "employees", "departments", "suppliers", "salary", "salaries", "budget",
    "cancelled", "pending", "status", "payment method", "sales",
    "كم عدد", "احسب", "قائمة", "اعلى", "ارخص", "الموظفين", "العملاء", "المنتجات", "الطلبات"
}

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

    if not has_conn and not has_kb:
        return "general"

    # 1. Instant short-circuit when user explicitly selects only DB or only KB
    if has_conn and not has_kb:
        return "database"
    if has_kb and not has_conn:
        return "document"

    msg_lower = user_message.lower()

    # 2. Fast Keyword Heuristic Checks
    # Explicit hybrid request check
    is_hybrid_query = any(k in msg_lower for k in HYBRID_TRIGGER_KEYWORDS)
    if is_hybrid_query and has_conn and has_kb:
        logger.info(f"Fast heuristic classifier matched HYBRID intent for: '{user_message}'")
        return "hybrid"

    # Explicit DB query check
    is_db_query = any(k in msg_lower for k in DATABASE_TRIGGER_KEYWORDS)
    is_doc_query = any(k in msg_lower for k in DOCUMENT_TRIGGER_KEYWORDS)

    if is_doc_query and has_kb and not is_hybrid_query:
        logger.info(f"Fast heuristic classifier matched DOCUMENT intent for: '{user_message}'")
        return "document"

    if is_db_query and has_conn and not is_doc_query:
        logger.info(f"Fast heuristic classifier matched DATABASE intent for: '{user_message}'")
        return "database"


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
            system_prompt=CLASSIFIER_SYSTEM_PROMPT,
            max_tokens=20,
        )
        
        # Clean output
        intent = raw_output.strip().lower()
        intent = re.sub(r"[^a-z]", "", intent)
        
        valid_intents: set[IntentType] = {"database", "document", "hybrid", "general", "clarification"}
        if intent in valid_intents:
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

    # Fallback default: prefer database if DB is connected, otherwise document
    if has_conn:
        return "database"
    elif has_kb:
        return "document"
    
    return "general"


