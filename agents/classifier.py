import re
from uuid import UUID

from schemas.chat import IntentType


DB_KEYWORDS = frozenset({
    "select", "sql", "query", "table", "tables", "column", "columns", "row", "rows",
    "database", "db", "count", "sum", "avg", "min", "max", "where", "join", "joins",
    "group", "order", "filter", "records", "schema", "schemas", "primary", "foreign",
    "insert", "update", "delete", "from", "knowledge_base", "knowledge_bases", "knowledgebase"
})

DOC_KEYWORDS = frozenset({
    "document", "documents", "doc", "docs", "pdf", "file", "files", "page", "pages",
    "article", "report", "reports", "section", "paragraph", "summary", "summarize",
    "text", "content", "excerpt", "policy", "manual", "attachment",
    "citation", "evidence", "read"
})


def classify_request(
    user_message: str,
    database_connection_ids: list[UUID] | None = None,
    knowledge_base_ids: list[UUID] | None = None,
) -> IntentType:
    """Classify user request into one of: general, database, document, hybrid, clarification."""
    msg_lower = user_message.strip().lower()
    has_conn = bool(database_connection_ids)
    has_kb = bool(knowledge_base_ids)

    # Greetings & General queries check FIRST
    greetings = {
        "hi", "hello", "hey", "howdy", "who are you", "what can you do", "help", "welcome",
        "مرحبا", "ازيك", "السلام عليكم", "مساعدة", "اهلا"
    }
    
    # Strip punctuation for cleaner greeting matching
    import string
    msg_clean = msg_lower.translate(str.maketrans('', '', string.punctuation)).strip()
    
    if msg_clean in greetings or any(msg_clean.startswith(g) for g in ["hi ", "hello ", "hey ", "مرحبا ", "ازيك ", "اهلا "]):
        return "general"

    tokens = set(re.findall(r"\b\w+\b", msg_lower))

    matches_db = bool(tokens & DB_KEYWORDS)
    matches_doc = bool(tokens & DOC_KEYWORDS)

    if matches_db and matches_doc:
        return "hybrid"
    elif matches_db:
        return "database"
    elif matches_doc:
        return "document"
    elif has_conn and has_kb:
        return "hybrid"
    elif has_conn:
        return "database"
    elif has_kb:
        return "document"
    elif len(msg_lower) < 3:
        return "clarification"

    return "general"



