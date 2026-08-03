# 16. Conversation and Messaging Persistence

## Goal

Persist tenant-scoped conversations and chat messages so users can resume authorized work, the graph can load bounded history, and answer traceability can link messages to query executions and citations without retaining unapproved source business records.

## Depends On

- [ ] Phase 02 provides conversations and messages schema models, migrations, indexes, and tenant constraints.
- [ ] Phase 03 provides authenticated tenant/user context.
- [ ] Phase 15 provides normalized graph inputs, outputs, status transitions, and timing data.
- [ ] Phase 17 provides citation linkage for completed assistant messages.

## Assignment References

- [ ] Sections 2, 5, 7.8, 7.9, 7.10, 8, 9, 10, 15, and 17.

## Detailed Tasks

- [ ] Implement tenant-scoped repositories for conversations and messages that always filter by trusted tenant_id before applying a conversation or message ID.
- [ ] Map every conversations field exactly: id, tenant_id, user_id, title, status, active_connection_ids, active_knowledge_base_ids, settings, created_at, updated_at, and last_message_at.
- [ ] Map every messages field exactly: id, tenant_id, conversation_id, parent_message_id, role, message_type, content, structured_content, detected_intent, selected_sources, model_name, prompt_tokens, completion_tokens, latency_ms, status, error_message, and created_at.
- [ ] Define a conversation creation service for POST /api/conversations that assigns the authenticated user and tenant, validates selected source IDs when present, initializes permitted settings, and emits an audit event.
- [ ] Define paginated tenant-scoped conversation listing for GET /api/conversations without exposing cross-tenant titles, timestamps, source selections, or user IDs.
- [ ] Define GET /api/conversations/{id} to validate ownership, return authorized conversation/message history, and omit internal-only execution secrets and hidden metadata.
- [ ] Define DELETE /api/conversations/{id} with tenant ownership verification, a documented retention/deletion policy for linked messages/citations/query records, and an audit event.
- [ ] Persist each user question before orchestration with role=user, message_type=text, selected requested sources, and a pending/running status where applicable.
- [ ] Persist each assistant answer after graph completion with role=assistant, exact detected intent, selected_sources, structured response metadata, model/token metrics when available, latency, and completed or failed status.
- [ ] Store only grounded answer text and allowed structured metadata; do not copy raw source rows, credentials, full document payloads, hidden schemas, or unmasked sensitive values into messages.
- [ ] Define bounded recent-history loading for the graph using an ordered count/token policy from conversation settings; do not expose another user's conversation unless an explicitly documented tenant-admin policy permits it.
- [ ] Link completed assistant message IDs to query_executions and message_citations through their existing foreign keys rather than duplicating SQL or document chunk content in messages.
- [ ] Define safe state transitions for pending, processing, completed, failed, and cancelled operations; retain a user-safe error message and keep detailed diagnostics in protected audit/observability channels.
- [ ] Update conversations.last_message_at and updated_at atomically with successful message writes.
- [ ] Add response schemas that preserve Section 9 chat response fields while keeping persistence-only fields out of public responses unless an endpoint requires them.

## Data Model Touched

- [ ] conversations.
- [ ] messages.
- [ ] query_executions.message_id and query_executions.conversation_id.
- [ ] message_citations.message_id.
- [ ] audit_logs for conversation lifecycle actions.

## API Endpoints Touched

- [ ] POST /api/conversations.
- [ ] GET /api/conversations.
- [ ] GET /api/conversations/{id}.
- [ ] DELETE /api/conversations/{id}.
- [ ] POST /api/chat and POST /api/chat/stream persist request/assistant messages.

## Security & Permission Notes

- [ ] Scope every read/write/delete by trusted tenant_id and validate the authenticated user can access the conversation.
- [ ] Treat active connection and knowledge-base ID arrays as untrusted until each referenced resource is tenant-authorized.
- [ ] Do not return internal error details, token prompts, encrypted credentials, row filters, or restricted result data in conversation APIs.

## Testing Requirements

- [ ] Unit-test tenant-scoped repository predicates and conversation ownership checks.
- [ ] Integration-test create/list/get/delete lifecycle for two tenants with overlapping-looking IDs or titles.
- [ ] Test message linkage to a successful database, document, and hybrid chat response.
- [ ] Test failed/cancelled graph persistence and safe error serialization.
- [ ] Test bounded history selection and exclusion of unauthorized or sensitive structured data.

## Definition of Done

- [ ] All required conversation endpoints enforce tenant ownership.
- [ ] User and assistant messages persist with traceable statuses and timestamps.
- [ ] Chat persistence does not become a store of raw source-database records.
- [ ] Conversation history is usable by the orchestrator and safe for public APIs.

## Suggested Day (1–4)

Day 4
