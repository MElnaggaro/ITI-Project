# 18. Streaming Chat API (SSE)

## Goal

Provide a safe Server-Sent Events interface for chat progress and answer delivery while preserving the non-streaming Section 9 response contract as the final authoritative result.

## Depends On

- [ ] Phase 03 provides authentication and request tenant context.
- [ ] Phase 15 provides graph lifecycle callbacks, cancellation, and normalized final states.
- [ ] Phase 16 provides message lifecycle persistence.
- [ ] Phase 17 provides final verified citations and SQL traceability data.
- [ ] Phase 19 provides request IDs, telemetry, and safe error handling.

## Assignment References

- [ ] Sections 5, 8, 9, 11, 14, and 15.

## Detailed Tasks

- [ ] Implement POST /api/chat/stream as an authenticated SSE endpoint using the same request validation, tenant checks, source selection, and graph path as POST /api/chat.
- [ ] Document the SSE event framing as a Baseline assumption because the PDF requires SSE but does not define event names or payloads.
- [ ] Emit a meta event after request validation with message_id, safe request identifier, and initial intent/status when known.
- [ ] Emit token events containing only answer deltas approved for the current assistant message; never stream hidden prompts, raw source rows, credentials, filter definitions, or internal traces.
- [ ] Emit one final event containing the complete Section 9-compatible response object after citations, SQL metadata, and message persistence have completed.
- [ ] Emit a safe error event with a stable public error code/message for validation, authorization, execution, retrieval, timeout, cancellation, or provider failures.
- [ ] Define keepalive behavior and response headers appropriate to SSE proxies without exposing internal diagnostics.
- [ ] Respect client disconnect and cancellation signals; cancel downstream work when safe, persist a cancelled/failed state, and avoid producing a false completed answer.
- [ ] Define backpressure and buffering rules so token streaming cannot bypass result-size, timeout, tenant, or masking controls.
- [ ] Ensure stream=true in the Section 9 request is documented consistently with POST /api/chat/stream; the selected routing convention must be recorded as a Baseline assumption in Phase 00.
- [ ] Reuse the same final response serializer as non-streaming chat so field names, citation shapes, and SQL details cannot drift.
- [ ] Add request IDs and per-event timing to protected telemetry, with token content excluded or redacted according to logging policy.

## Data Model Touched

- [ ] messages status, content, latency_ms, error_message, and created_at.
- [ ] conversations last_message_at and updated_at.
- [ ] query_executions and message_citations are read for the final event.
- [ ] audit_logs for stream start, completion, cancellation, and failure.

## API Endpoints Touched

- [ ] POST /api/chat/stream.
- [ ] POST /api/chat shares request/response serialization rules.

## Security & Permission Notes

- [ ] Authenticate before opening an event stream and carry trusted tenant context through every callback.
- [ ] Never stream an answer before authorization, SQL validation, document filtering, and sensitive-value masking have occurred.
- [ ] Public error events are intentionally generic; full diagnostics remain protected.

## Testing Requirements

- [ ] Integration-test authenticated SSE headers, meta/token/final sequence, and final Section 9 response compatibility.
- [ ] Test document, database, hybrid, general, and clarification streaming paths.
- [ ] Test disconnect/cancellation, timeout, validation failure, and retrieval failure event sequences.
- [ ] Test cross-tenant source selection and sensitive data cannot appear in any event payload.
- [ ] Test non-streaming and final streaming response serializers return equivalent normalized data.

## Definition of Done

- [ ] POST /api/chat/stream safely streams authorized progress and a complete final response.
- [ ] Disconnects and failures persist accurate message states.
- [ ] SSE behavior is documented as a baseline extension where the PDF is silent.

## Suggested Day (1–4)

Day 4
