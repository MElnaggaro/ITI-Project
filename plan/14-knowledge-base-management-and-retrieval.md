# 14. Knowledge Base Management & Retrieval

## Goal

Provide tenant-scoped knowledge-base management and a server-owned document retrieval service that selects only authorized, processed document chunks, reranks evidence, and returns citation-ready provenance to the chat orchestrator. It must never allow a client or LLM to search another tenant’s files or supply unrestricted vector filters.

## Depends On

- [x] Phase 03 provides authenticated tenant and user context.
- [x] Phase 04 provides tenant resource authorization rules.
- [x] Phase 11 provides tenant-scoped files and knowledge-base association lifecycle.
- [x] Phase 12 provides completed chunks and safe processing status.
- [x] Phase 13 provides Qdrant indexing, model compatibility, and enforced vector-store filters.

## Assignment References

- [x] Section 2: document chat capability and cited document evidence.
- [x] Section 3: Document RAG Agent, query rewriter, vector retriever, and evidence reranker.
- [x] Section 5, steps 2, 3, 6, and 8: load selected knowledge bases, classify requests, retrieve/rerank evidence, and use approved outputs.
- [x] Sections 7.6 through 7.8: knowledge_bases, files, document_chunks, conversations, and messages.
- [x] Section 8: knowledge-base endpoints.
- [x] Section 9: citations in the chat response.
- [x] Sections 13 through 15: Day 3 scope, document chat, citations, and acceptance criteria.

## Detailed Tasks

- [x] Implement POST /api/knowledge-bases to create a tenant-scoped knowledge base with name, optional description, selected 1024-dimension embedding model, server-validated chunking configuration, creator identity, and timestamps.
- [x] Implement GET /api/knowledge-bases with tenant-scoped listing and safe summary fields; do not expose another tenant’s IDs, file metadata, or storage/index details.
- [x] Define the baseline behavior of POST /api/knowledge-bases/{id}/files: authorize the knowledge base and file in the same tenant, attach or queue the file using the Phase 11 lifecycle, and document the request payload because Section 8 specifies the path but not its wire shape.
- [x] Validate knowledge-base names against the tenant-scoped unique constraint and return stable conflict/validation errors without internal database details.
- [x] Build an internal retrieval request containing authenticated tenant_id/user_id, explicitly selected authorized knowledge_base_ids, user question, request correlation ID, and configured result budget; do not accept arbitrary Qdrant filters or file IDs as authorization proof.
- [x] Reject selected knowledge bases that are missing, cross-tenant, unauthorized, or have no completed/indexed files; return a safe clarification or unavailable-source state to the orchestrator.
- [x] Implement query rewriting as an internal RAG step that preserves the tenant/knowledge-base constraints and never adds sources selected by the LLM.
- [x] Generate query embeddings using the matching knowledge-base model/version and partition retrieval by model when selected knowledge bases use incompatible embedding spaces.
- [x] Query Qdrant only through the server-owned client with mandatory tenant_id, selected knowledge_base_ids, completed-file state, and compatible model-version filters plus bounded top-k/score thresholds.
- [x] Load chunk content and provenance from PostgreSQL only for returned, still-authorized chunk IDs; recheck tenant, knowledge-base, file status, and deletion/reprocess state before exposing evidence.
- [x] Rerank the bounded candidate set with a controlled evidence-reranker and return only approved evidence records containing chunk ID, file ID/name, page/section metadata, score, and safe excerpts needed for grounded answering.
- [x] Ensure document-answer generation later receives only retrieved approved chunks, not whole knowledge bases or arbitrary document text; Phase 17 persists citations and Phase 15 produces final answers.
- [x] Use conversations.active_knowledge_base_ids as a tenant-authorized persisted selection, validating it on every chat request rather than trusting stale IDs.
- [x] Emit sanitized retrieval metrics/audit events for selected sources, candidate/result counts, latency, and failures without logging raw documents or cross-tenant identifiers.

## Data Model Touched

- [x] Create/read knowledge_bases.id, tenant_id, created_by, name, description, embedding_model, chunking_config, created_at, and updated_at.
- [x] Read/update files.knowledge_base_id and processing state through the authorized association lifecycle.
- [x] Read document_chunks tenant_id, knowledge_base_id, file_id, content, page_number, section_title, metadata, and lifecycle/model metadata after vector-filtered ID retrieval.
- [x] Read/update conversations.active_knowledge_base_ids and messages.selected_sources as later conversation/chat phases persist selections.
- [x] Do not persist final message_citations in this phase; Phase 17 owns citation persistence and endpoint traceability.

## API Endpoints Touched

- [x] POST /api/knowledge-bases.
- [x] GET /api/knowledge-bases.
- [x] POST /api/knowledge-bases/{id}/files.

## Security & Permission Notes

- [x] Enforce tenant ownership and authorization for every knowledge-base create, list, attach, selection, retrieval, and evidence-read operation.
- [x] Keep tenant/knowledge-base filtering backend-owned through the Qdrant and PostgreSQL service boundaries; neither LLM prompts nor clients can widen it.
- [x] Return only bounded citation-ready excerpts and metadata, not complete document corpora, storage paths, provider credentials, or internal retrieval traces.
- [x] Preserve data-residency separation: retrieval indexes uploaded document chunks, never copied live customer-database business records.

## Testing Requirements

- [x] Integration-test create/list/attach knowledge-base endpoints for validation, uniqueness, authorization, and tenant isolation.
- [x] Test retrieval with selected valid knowledge bases, empty/processing knowledge bases, cross-tenant IDs, deleted files, stale vectors, and incompatible embedding models.
- [x] Test mandatory Qdrant filters plus PostgreSQL reauthorization so forged IDs, LLM-selected sources, and stale payloads cannot disclose another tenant’s chunks.
- [x] Test bounded candidate retrieval, reranking, citation-ready file/page/section provenance, and no whole-document exposure.
- [x] Test conversation knowledge-base selections are revalidated on each request and retrieval logs remain sanitized.

## Definition of Done

- [x] Tenants can create, list, and associate authorized knowledge bases through the required endpoints.
- [x] The internal retrieval service returns only tenant-authorized, processed, model-compatible, reranked evidence with citation-ready provenance.
- [x] No client, LLM, or stale vector record can widen source selection across tenants or expose full document corpora.

## Suggested Day (1–4)

Day 3.
