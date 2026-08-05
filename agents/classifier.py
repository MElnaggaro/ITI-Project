import re
import string
from uuid import UUID

from schemas.chat import IntentType


DB_KEYWORDS = frozenset({
    # SQL operations
    "select", "sql", "query", "table", "tables", "column", "columns", "row", "rows",
    "database", "db", "count", "sum", "avg", "min", "max", "where", "join", "joins",
    "group", "order", "filter", "records", "schema", "schemas", "primary", "foreign",
    "insert", "update", "delete", "from",
    # Platform entity names (tables that exist in the database)
    "users", "tenants", "roles", "connections", "conversations", "messages",
    "files", "knowledge_bases", "knowledgebase", "knowledge_base",
    "executions", "permissions", "audit", "chunks",
    # Database action words
    "list", "show", "display", "total", "active", "inactive", "assigned",
    "size", "status", "processing",
    # Aggregation / analytics phrasing
    "how many", "how much", "number of", "average", "biggest", "smallest",
    "most", "least", "recent", "latest", "oldest",
})

DOC_KEYWORDS = frozenset({
    "document", "documents", "doc", "docs", "pdf",
    "page", "pages", "article", "report", "reports",
    "section", "paragraph", "summary", "summarize",
    "policy", "manual", "attachment", "handbook",
    "citation", "evidence", "read", "guideline", "guidelines",
    "procedure", "requirement", "requirements", "specification",
    "architecture", "encrypt", "encryption", "security",
    "leave", "pto", "vacation", "remote", "sdlc",
    "technova", "company", "employee", "employees",
})

# Phrases that strongly indicate a database query over document search
DB_ACTION_PATTERNS = [
    r"\b(list|show|display|get|fetch|find)\b.*\b(all|every|each)\b",
    r"\b(how many|count|total|number of)\b",
    r"\b(active|inactive|enabled|disabled)\b.*\b(connections?|users?|tenants?|roles?)\b",
    r"\bwith their\b",
    r"\b(assigned|uploaded|processing|file.?size)\b",
]


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
    msg_clean = msg_lower.translate(str.maketrans('', '', string.punctuation)).strip()
    
    if msg_clean in greetings or any(msg_clean.startswith(g) for g in ["hi ", "hello ", "hey ", "مرحبا ", "ازيك ", "اهلا "]):
        return "general"

    tokens = set(re.findall(r"\b\w+\b", msg_lower))

    matches_db = bool(tokens & DB_KEYWORDS)
    matches_doc = bool(tokens & DOC_KEYWORDS)

    # Check for strong DB action patterns (overrides doc classification)
    has_db_action = any(re.search(p, msg_lower) for p in DB_ACTION_PATTERNS)

    if has_db_action and matches_db:
        # Strong DB signal: action verb + DB keyword → always database
        return "database"
    elif matches_db and matches_doc:
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


