# 12. Document Parsing & Chunking

## Goal

Asynchronously transform authorized uploaded files into tenant-scoped, provenance-preserving document chunks that can be embedded and retrieved later. Parsing must support the assignment’s file types, preserve citation-relevant metadata, handle failures safely, and remain idempotent for retries and reprocessing.

## Depends On

- [x] Phase 01 provides Celery/Redis worker infrastructure and configuration.
- [x] Phase 03 provides serializable tenant context for worker jobs.
- [x] Phase 11 provides validated file metadata, MinIO object access, lifecycle states, and reprocess jobs.
- [x] Phase 13 consumes the completed chunks for embedding/indexing.

## Assignment References

- [x] Section 2: parse, chunk, embed, and index supported files.
- [x] Section 3: Document RAG Agent and File Upload and Processing architecture.
- [x] Sections 4 and 7.6 through 7.7: document processor, chunking service, parsers, files, and document_chunks.
- [x] Section 5, steps 6 and 9: document evidence retrieval and persistence.
- [x] Section 11: Docling and format-specific parsers.
- [x] Sections 13 through 15: Day 3 scope, file-processing integration tests, citations, and document-processing acceptance criteria.

## Detailed Tasks

- [x] Define a Celery file-processing job that loads only the file ID and authenticated tenant context, rechecks tenant ownership and processing eligibility, and is safe to retry.
- [x] Fetch the original object through the server-side MinIO client; do not expose a bucket credential, signed URL secret, or object path to the worker logs or API response.
- [x] Dispatch parsing by validated type: PDF, Word, Excel, CSV, and text; use Docling where applicable and dedicated format parsers where Docling does not preserve required structure.
- [x] Normalize extracted text deterministically while preserving provenance such as file ID, page number, section title, workbook/sheet or tabular location metadata when available, and parser/version information.
- [x] Record page_count and extracted_text_length for successful extraction, and store only safe structured parser metadata in files.metadata.
- [x] Define a versioned chunking configuration sourced from knowledge_bases.chunking_config, with server-owned defaults for chunk size, overlap, separators, and token counting.
- [x] Split content into ordered chunks with stable chunk_index values, content hashes, token counts, citation-relevant page/section metadata, and tenant_id/knowledge_base_id/file_id on every document_chunks row.
- [x] Enforce configured maximum extraction size, chunk count, and token budget; fail safely rather than exhaust workers on pathological files.
- [x] Update files.processing_status through pending, processing, completed, and failed states, and store sanitized processing_error text without parser stack traces or document secrets.
- [x] Make duplicate upload, retry, and reprocess behavior idempotent using checksum/content hashes and controlled replacement of prior chunks and their later vector records.
- [x] Ensure reprocessing/deletion uses an ordered cleanup contract: prevent retrieval of stale chunks, delete or supersede old embeddings through Phase 13, then publish only the completed replacement set.
- [x] Emit correlated audit and job events containing file IDs, counts, safe status, and latency, but not extracted document bodies in logs.

## Data Model Touched

- [x] Update files.processing_status, processing_error, page_count, extracted_text_length, metadata, and processed_at.
- [x] Create/update/delete document_chunks.id, tenant_id, knowledge_base_id, file_id, chunk_index, content, content_hash, page_number, section_title, token_count, metadata, embedding, and created_at.
- [x] Read knowledge_bases.embedding_model and chunking_config to select compatible processing behavior.
- [x] Do not store live customer-database business data in document chunks or parser metadata.

## API Endpoints Touched

- [x] POST /api/files/{id}/reprocess invokes the asynchronous processing workflow supplied by this phase.
- [x] GET /api/files and GET /api/files/{id} expose safe processing status from this phase; they do not expose extracted content by default.

## Security & Permission Notes

- [x] Recheck tenant context in workers because queued work must not inherit authority solely from an untrusted payload.
- [x] Keep source object access, parser errors, extracted-content logs, and storage credentials private.
- [x] Preserve tenant_id and knowledge_base_id on every chunk so later embedding and retrieval enforce isolation at the data boundary.
- [x] Do not index a file until parsing/chunk persistence completes successfully and the status transition is durable.

## Testing Requirements

- [x] Integration-test parsing and chunk provenance for PDF, Word, Excel, CSV, and text fixtures.
- [x] Unit-test deterministic chunk boundaries, hashes, token counts, page/section metadata, and chunking configuration versions.
- [x] Test malformed/encrypted/oversized files, parser timeouts, retries, and safe failed-status/error behavior.
- [x] Test idempotent duplicate processing, reprocess replacement, delete cleanup coordination, and no stale chunk retrieval window.
- [x] Test tenant isolation in worker jobs and assert no extracted document body or storage secret appears in logs.

## Definition of Done

- [x] Every supported successful upload can become an ordered, tenant-scoped chunk set with citation-relevant provenance.
- [x] Failed parsing is visible through safe file status/error fields and can be retried or reprocessed without duplicate chunks.
- [x] Chunk records are ready for Phase 13 embedding without exposing storage credentials or cross-tenant content.

## Suggested Day (1–4)

Day 3.
