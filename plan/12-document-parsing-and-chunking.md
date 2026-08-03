# 12. Document Parsing & Chunking

## Goal

Asynchronously transform authorized uploaded files into tenant-scoped, provenance-preserving document chunks that can be embedded and retrieved later. Parsing must support the assignment’s file types, preserve citation-relevant metadata, handle failures safely, and remain idempotent for retries and reprocessing.

## Depends On

- [ ] Phase 01 provides Celery/Redis worker infrastructure and configuration.
- [ ] Phase 03 provides serializable tenant context for worker jobs.
- [ ] Phase 11 provides validated file metadata, MinIO object access, lifecycle states, and reprocess jobs.
- [ ] Phase 13 consumes the completed chunks for embedding/indexing.

## Assignment References

- [ ] Section 2: parse, chunk, embed, and index supported files.
- [ ] Section 3: Document RAG Agent and File Upload and Processing architecture.
- [ ] Sections 4 and 7.6 through 7.7: document processor, chunking service, parsers, files, and document_chunks.
- [ ] Section 5, steps 6 and 9: document evidence retrieval and persistence.
- [ ] Section 11: Docling and format-specific parsers.
- [ ] Sections 13 through 15: Day 3 scope, file-processing integration tests, citations, and document-processing acceptance criteria.

## Detailed Tasks

- [ ] Define a Celery file-processing job that loads only the file ID and authenticated tenant context, rechecks tenant ownership and processing eligibility, and is safe to retry.
- [ ] Fetch the original object through the server-side MinIO client; do not expose a bucket credential, signed URL secret, or object path to the worker logs or API response.
- [ ] Dispatch parsing by validated type: PDF, Word, Excel, CSV, and text; use Docling where applicable and dedicated format parsers where Docling does not preserve required structure.
- [ ] Normalize extracted text deterministically while preserving provenance such as file ID, page number, section title, workbook/sheet or tabular location metadata when available, and parser/version information.
- [ ] Record page_count and extracted_text_length for successful extraction, and store only safe structured parser metadata in files.metadata.
- [ ] Define a versioned chunking configuration sourced from knowledge_bases.chunking_config, with server-owned defaults for chunk size, overlap, separators, and token counting.
- [ ] Split content into ordered chunks with stable chunk_index values, content hashes, token counts, citation-relevant page/section metadata, and tenant_id/knowledge_base_id/file_id on every document_chunks row.
- [ ] Enforce configured maximum extraction size, chunk count, and token budget; fail safely rather than exhaust workers on pathological files.
- [ ] Update files.processing_status through pending, processing, completed, and failed states, and store sanitized processing_error text without parser stack traces or document secrets.
- [ ] Make duplicate upload, retry, and reprocess behavior idempotent using checksum/content hashes and controlled replacement of prior chunks and their later vector records.
- [ ] Ensure reprocessing/deletion uses an ordered cleanup contract: prevent retrieval of stale chunks, delete or supersede old embeddings through Phase 13, then publish only the completed replacement set.
- [ ] Emit correlated audit and job events containing file IDs, counts, safe status, and latency, but not extracted document bodies in logs.

## Data Model Touched

- [ ] Update files.processing_status, processing_error, page_count, extracted_text_length, metadata, and processed_at.
- [ ] Create/update/delete document_chunks.id, tenant_id, knowledge_base_id, file_id, chunk_index, content, content_hash, page_number, section_title, token_count, metadata, embedding, and created_at.
- [ ] Read knowledge_bases.embedding_model and chunking_config to select compatible processing behavior.
- [ ] Do not store live customer-database business data in document chunks or parser metadata.

## API Endpoints Touched

- [ ] POST /api/files/{id}/reprocess invokes the asynchronous processing workflow supplied by this phase.
- [ ] GET /api/files and GET /api/files/{id} expose safe processing status from this phase; they do not expose extracted content by default.

## Security & Permission Notes

- [ ] Recheck tenant context in workers because queued work must not inherit authority solely from an untrusted payload.
- [ ] Keep source object access, parser errors, extracted-content logs, and storage credentials private.
- [ ] Preserve tenant_id and knowledge_base_id on every chunk so later embedding and retrieval enforce isolation at the data boundary.
- [ ] Do not index a file until parsing/chunk persistence completes successfully and the status transition is durable.

## Testing Requirements

- [ ] Integration-test parsing and chunk provenance for PDF, Word, Excel, CSV, and text fixtures.
- [ ] Unit-test deterministic chunk boundaries, hashes, token counts, page/section metadata, and chunking configuration versions.
- [ ] Test malformed/encrypted/oversized files, parser timeouts, retries, and safe failed-status/error behavior.
- [ ] Test idempotent duplicate processing, reprocess replacement, delete cleanup coordination, and no stale chunk retrieval window.
- [ ] Test tenant isolation in worker jobs and assert no extracted document body or storage secret appears in logs.

## Definition of Done

- [ ] Every supported successful upload can become an ordered, tenant-scoped chunk set with citation-relevant provenance.
- [ ] Failed parsing is visible through safe file status/error fields and can be retried or reprocessed without duplicate chunks.
- [ ] Chunk records are ready for Phase 13 embedding without exposing storage credentials or cross-tenant content.

## Suggested Day (1–4)

Day 3.
