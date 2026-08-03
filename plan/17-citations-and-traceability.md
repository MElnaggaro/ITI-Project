# 17. Citations and Traceability

## Goal

Make every grounded answer traceable to authorized document chunks and/or a controlled SQL execution while returning the exact Section 9 citation shapes needed by clients.

## Depends On

- [ ] Phase 02 provides message_citations, query_executions, files, and document_chunks schema.
- [ ] Phase 10 provides completed execution identifiers, normalized SQL, safe previews, and referenced objects.
- [ ] Phase 14 provides retrieved chunks, file metadata, page/section metadata, and relevance scores.
- [ ] Phases 15 and 16 provide completed assistant message IDs and normalized answer data.

## Assignment References

- [ ] Sections 2, 5, 7.7, 7.9, 7.10, 8, 9, 10, 14, 15, and 17.

## Detailed Tasks

- [ ] Implement a tenant-scoped citation repository for message_citations that verifies the message, file, chunk, and execution resources belong to the same tenant before insertion or retrieval.
- [ ] Map every message_citations field exactly: id, tenant_id, message_id, citation_type, file_id, chunk_id, query_execution_id, title, source_reference, page_number, relevance_score, metadata, and created_at.
- [ ] Define document citation creation from approved retrieved chunks, preserving file identity, original file name, page number when available, section/source reference, and relevance score.
- [ ] Define database citation creation from an approved query execution, preserving query_execution_id and authorized referenced table information without exposing hidden schema or restricted columns.
- [ ] Require the final-answer generator to use only citation candidates supplied by retrieval/execution services; it must not invent file names, pages, tables, execution IDs, or relevance claims.
- [ ] Transform stored citations into the Section 9 contract: document citations expose type=document, file_name, and page when available; database citations expose type=database and table.
- [ ] Define the response baseline for a non-database answer as no SQL object or an explicitly documented null SQL value; do not invent a query execution ID.
- [ ] Implement GET /api/messages/{id}/citations with tenant/message ownership validation, source-appropriate public fields, pagination if needed, and no hidden chunk content by default.
- [ ] Implement GET /api/messages/{id}/sql with tenant/message ownership validation, an authorized query_execution lookup, generated/normalized SQL and safe execution metadata, and no credentials or unrestricted result rows.
- [ ] Link citation persistence and query execution persistence atomically where possible so a completed answer cannot point to a non-existent or cross-tenant source.
- [ ] Record citation creation/retrieval events in audit logs through Phase 19 without logging full chunk text or sensitive source values.
- [ ] Define retention/deletion behavior so deleted files/conversations follow the Section 7 foreign-key behavior and public endpoints handle missing sources safely.

## Data Model Touched

- [ ] message_citations.
- [ ] messages.
- [ ] query_executions.
- [ ] files.
- [ ] document_chunks.
- [ ] audit_logs.

## API Endpoints Touched

- [ ] GET /api/messages/{id}/citations.
- [ ] GET /api/messages/{id}/sql.
- [ ] POST /api/chat and POST /api/chat/stream return citations and SQL details in their final response.

## Security & Permission Notes

- [ ] Citation access is tenant-scoped and tied to message ownership/authorization.
- [ ] Citation metadata must not expose excluded document text, sensitive database columns, encrypted paths, credentials, or cross-tenant resource identifiers.
- [ ] Database table citations are derived from validated execution metadata, not LLM-generated strings.

## Testing Requirements

- [ ] Unit-test public citation serialization for document-only, database-only, hybrid, and no-source responses.
- [ ] Integration-test citation persistence and retrieval across documents, query executions, and assistant messages.
- [ ] Test cross-tenant and cross-conversation citation/message ID access is rejected.
- [ ] Test missing/deleted file or execution behavior is safe and does not leak metadata.
- [ ] Test that fabricated LLM citation values are rejected or replaced only by verified source metadata.

## Definition of Done

- [ ] Every grounded answer can be traced to a persisted document chunk and/or query execution.
- [ ] Citation response shapes match the Section 9 source-specific contract.
- [ ] Citation and SQL lookup endpoints are tenant-isolated and redact sensitive internals.

## Suggested Day (1–4)

Day 4
