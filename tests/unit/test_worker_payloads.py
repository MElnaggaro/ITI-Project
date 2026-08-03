"""Worker payload boundary tests."""

from uuid import uuid4

import pytest

from workers.payloads import WorkerTaskContext, validate_worker_payload


def test_worker_context_contains_only_identifiers() -> None:
    context = WorkerTaskContext(
        tenant_id=uuid4(),
        resource_id=uuid4(),
        request_id="request-123",
    )

    assert context.request_id == "request-123"


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "not-allowed"},
        {"nested": {"connection_string": "not-allowed"}},
        {"source_rows": [{"id": 1}]},
        {"query_result": {"rows": ["not-allowed"]}},
    ],
)
def test_worker_payload_rejects_secrets_and_source_results(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="forbidden"):
        validate_worker_payload(payload)
