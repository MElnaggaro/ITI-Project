"""Logging redaction tests."""

from app.logging_config import REDACTED, redact_value


def test_redact_value_removes_nested_secrets() -> None:
    payload = {
        "connection_string": "postgres://secret",
        "nested": {"token": "token-value", "safe": "value"},
    }

    assert redact_value(payload) == {
        "connection_string": REDACTED,
        "nested": {"token": REDACTED, "safe": "value"},
    }
