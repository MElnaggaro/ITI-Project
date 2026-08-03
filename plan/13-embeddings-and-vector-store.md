# 13. Embeddings & Vector Store

## Goal

Embed completed document chunks with a dimension-compatible model and index them in Qdrant for tenant-filtered semantic retrieval. Qdrant is the canonical retrieval store; the required PostgreSQL pgvector extension and document_chunks.embedding VECTOR(1024) field remain in the schema for assignment compatibility but are not a second production retrieval index.

## Depends On

- [x] Phase 01 provides PostgreSQL with the required vector extension, Qdrant, worker configuration, and secret management.
- [x] Phase 11 provides durable file lifecycle and deletion/reprocess events.
- [x] Phase 12 provides completed tenant-scoped chunks with stable IDs, content hashes, provenance, and processing status.
- [x] Phase 14 consumes indexed Qdrant records through a server-owned retrieval interface.

## Assignment References

- [x] Section 2: embedding and indexing file ingestion.
- [x] Section 3: Vector DB and Document RAG Agent components.
- [x] Sections 7.1 and 7.7: vector extension and document_chunks.embedding VECTOR(1024).
- [x] Section 11: pgvector or Qdrant option; Qdrant is the selected retrieval baseline.
- [x] Section 12: qdrant deployment service.
- [x] Sections 13 through 15: Day 3 vector retrieval scope and document-processing acceptance criteria.
- [x] Section 17: Vector Database stores embeddings for uploaded document chunks.

## Detailed Tasks

- [x] Select and pin a 1024-dimension embedding model compatible with document_chunks.embedding VECTOR(1024); validate every provider response dimension before persistence or Qdrant upsert.
- [x] Store the selected model identifier and version in knowledge_bases.embedding_model and chunk metadata so queries never silently compare incompatible embedding spaces.
- [x] Configure Qdrant as the canonical semantic-retrieval index for this baseline and use PostgreSQL only for authoritative chunk metadata/content and the required schema field.
- [x] Retain the required pgvector extension and document_chunks.embedding VECTOR(1024) column, but leave that field unpopulated in the Qdrant baseline to avoid divergent duplicate indexes; any future mirror policy requires an explicit migration, reconciliation strategy, and tests.
- [x] Define a versioned Qdrant collection strategy with vectors of size 1024 and payload limited to chunk ID, tenant ID, knowledge-base ID, file ID, processing/model version, and safe retrieval metadata.
- [x] Do not place raw file contents, source database records, credentials, or unmasked sensitive values into Qdrant payloads; load chunk content from PostgreSQL only after tenant-authorized result IDs are returned.
- [x] Build an idempotent embedding worker that reads only completed chunks, batches requests within configured size/rate limits, validates dimensions, and upserts vectors using stable document_chunk IDs.
- [x] Apply mandatory tenant and knowledge-base payload filters in the server-owned Qdrant client for every search, update, and delete operation; clients and LLMs never provide unrestricted vector filters.
- [x] Track embedding/index status through file/chunk metadata or controlled job state so a partially indexed file cannot be reported as fully searchable.
- [x] On model change, dimension mismatch, reprocess, or deletion, version/rebuild or remove affected vectors deterministically and prevent mixing vectors from incompatible models in one query.
- [x] Implement retry, backoff, dead-letter/error status, and idempotent reconciliation for embedding-provider and Qdrant failures without logging chunk bodies or provider secrets.
- [x] Emit sanitized metrics/audit events for counts, latency, dimension validation, upserts, deletes, and failures.

## Data Model Touched

- [x] Preserve the Section 7.1 vector extension and Section 7.7 document_chunks.embedding VECTOR(1024) field in migrations.
- [x] Read/update document_chunks IDs, tenant_id, knowledge_base_id, file_id, content_hash, metadata, and embedding lifecycle metadata; do not create a second ungoverned vector source of truth.
- [x] Read/update knowledge_bases.embedding_model and use chunking_config/model metadata to maintain index compatibility.
- [x] Read files processing state to prevent indexing failed, deleted, or incomplete documents.

## API Endpoints Touched

- [x] No Section 8 endpoint is implemented directly in this phase; indexing is asynchronous after upload/processing and retrieval is exposed internally to Phase 14.
- [x] Do not expose Qdrant administration or arbitrary vector-search endpoints to clients.

## Security & Permission Notes

- [x] Enforce tenant and knowledge-base scoping inside the vector-store service rather than trusting client, worker, or LLM filter input.
- [x] Keep Qdrant credentials, embedding-provider credentials, raw chunk content, and source database data out of API responses and logs.
- [x] Fail a mismatched embedding dimension closed; never truncate, pad, or silently coerce a vector to fit VECTOR(1024).
- [x] Treat embedding lifecycle events as tenant-scoped auditable operations.

## Testing Requirements

- [x] Unit-test 1024-dimension acceptance and deterministic rejection of short, long, null, malformed, and model-mismatched embeddings.
- [x] Integration-test Qdrant upsert/search/delete with tenant and knowledge-base filters, asserting cross-tenant chunks cannot be returned.
- [x] Test idempotent retries, duplicate chunk upserts, reprocess replacement, deletion cleanup, and reconciliation after partial failure.
- [x] Test model-version changes and ensure incompatible embeddings are not searched together.
- [x] Test that Qdrant payloads and logs contain only approved identifiers/metadata, not raw chunk bodies, secrets, or customer database rows.

## Definition of Done

- [x] Completed document chunks are indexed in Qdrant with a validated 1024-dimension model and mandatory tenant/knowledge-base filters.
- [x] PostgreSQL retains the required pgvector schema field without becoming an inconsistent second retrieval index.
- [x] Indexing, deletion, and reprocessing are idempotent, observable, and safe across tenant boundaries.

## Suggested Day (1–4)

Day 3.
