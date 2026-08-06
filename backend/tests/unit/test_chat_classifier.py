"""Unit tests for chat intent classifier."""

from uuid import uuid4

from agents.classifier import classify_request


def test_classify_request_intents():
    """Verify request intent classification across general, database, document, hybrid, clarification."""
    # 1. Database intent by keywords or database_connection_ids
    assert classify_request("SELECT * FROM orders") == "database"
    assert classify_request("Show total sales", database_connection_ids=[uuid4()]) == "database"

    # 2. Document intent by keywords or knowledge_base_ids
    assert classify_request("Summarize company report PDF") == "document"
    assert classify_request("Search policy file", knowledge_base_ids=[uuid4()]) == "document"

    # 3. Hybrid intent
    assert classify_request("Compare sales database with PDF report", database_connection_ids=[uuid4()], knowledge_base_ids=[uuid4()]) == "hybrid"

    # 4. General intent
    assert classify_request("Hello, how are you?") == "general"

    # 5. Clarification intent
    assert classify_request("a") == "clarification"
