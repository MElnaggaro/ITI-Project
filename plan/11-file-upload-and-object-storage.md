# 11. File Upload & Object Storage

## Goal

Provide tenant-scoped, secure upload and file-lifecycle APIs for knowledge-base documents, storing original files in MinIO and durable metadata in PostgreSQL before asynchronous processing. The phase supports PDF, Word, Excel, CSV, and text files without exposing one tenant’s files or storage paths to another.

## Depends On

- [x] Phase 01 provides MinIO configuration, application configuration, worker infrastructure, and Docker service definitions.
- [x] Phase 03 provides authenticated user and tenant context.
- [x] Phase 04 provides authorization primitives for tenant administration and resource ownership.
- [x] Phase 13 later supplies vector-index cleanup; upload/delete contracts must expose the lifecycle hooks it needs.

## Assignment References

- [x] Section 2: File ingestion capability.
- [x] Section 3: File Upload and Processing and Object Storage components.
- [x] Sections 4 and 7.6: files route/module and files table.
- [x] Section 8: file and knowledge-base file endpoints.
- [x] Section 11: MinIO, S3, or Azure Blob Storage option; MinIO is the selected baseline.
- [x] Sections 13 through 15: Day 3 scope, file-processing tests, document-processing acceptance criteria, and tenant isolation.

## Detailed Tasks

- [x] Configure MinIO as the selected object-store baseline with credentials supplied only through environment configuration and never returned by APIs or logs.
- [x] Define allowed upload types for PDF, Word documents, Excel workbooks, CSV, and plain-text files; document the accepted MIME types and extensions, including DOC/DOCX and XLS/XLSX where supported.
- [x] Implement POST /api/files/upload as authenticated multipart upload that resolves tenant context server-side, validates file type and configured size limits, computes a checksum, and optionally associates the file with an authorized knowledge base.
- [x] Validate both declared MIME type and inspected file signature/content where feasible; reject unsupported, empty, malformed, or oversized uploads with stable safe errors.
- [x] Generate stored_name and storage_path server-side using non-guessable identifiers and tenant-scoped object prefixes; never use the client original_name as an object key.
- [x] Persist files metadata with tenant_id, knowledge_base_id, uploaded_by, original_name, stored_name, storage_path, MIME/extension, size, checksum, processing_status, and timestamps.
- [x] Set a durable pending processing state only after the object write and metadata transaction have succeeded; enqueue an idempotent Celery processing job that carries file ID and tenant context rather than file bytes or secrets.
- [x] Implement GET /api/files and GET /api/files/{id} with tenant-scoped filtering, pagination/status filtering where needed, and metadata responses that never disclose another tenant’s file or raw storage credentials.
- [x] Implement DELETE /api/files/{id} as an authorized lifecycle operation that marks/removes the metadata and coordinates object, chunk, and vector-index cleanup without allowing cross-tenant deletion.
- [x] Implement POST /api/files/{id}/reprocess to authorize the file, reset it to a safe pending state, and enqueue an idempotent reprocessing workflow; do not synchronously parse large files in the API request.
- [x] Define POST /api/knowledge-bases/{id}/files as the baseline association operation for an authorized tenant knowledge base; document its exact request shape as an implementation assumption because Section 8 supplies only the path.
- [x] Record upload, deletion, association, and reprocess audit events with request/user/file IDs and sanitized metadata.
- [x] Return processing status and safe errors rather than parser traces, object-store credentials, internal bucket names, or filesystem paths.

## Data Model Touched

- [x] Create/read/update/delete files fields from Section 7.6, including tenant_id, knowledge_base_id, uploaded_by, original_name, stored_name, storage_path, MIME/extension, checksum, processing_status, processing_error, page_count, extracted_text_length, metadata, created_at, and processed_at.
- [x] Read knowledge_bases.id and tenant_id to authorize association.
- [x] Coordinate later cleanup of document_chunks and external Qdrant vectors without storing their payloads in file API responses.
- [x] Emit audit_logs for file lifecycle operations.

## API Endpoints Touched

- [x] POST /api/files/upload.
- [x] GET /api/files.
- [x] GET /api/files/{id}.
- [x] DELETE /api/files/{id}.
- [x] POST /api/files/{id}/reprocess.
- [x] POST /api/knowledge-bases/{id}/files.

## Security & Permission Notes

- [x] Resolve tenant_id and user identity from authentication, never from a mutable request field.
- [x] Enforce authorization before object reads, writes, associations, reprocesses, deletes, and metadata responses.
- [x] Use tenant-scoped object keys, non-guessable stored names, server-side size/type limits, and secret-free error/log handling.
- [x] Uploaded documents are tenant knowledge-base content; do not mix them with business data copied from live customer databases.

## Testing Requirements

- [x] Integration-test uploads for PDF, Word, Excel, CSV, and text fixtures, plus rejected unsupported MIME, spoofed extension, empty, and oversized files.
- [x] Test object-key generation, metadata persistence, checksum handling, and queued job payloads for tenant context without file-byte duplication.
- [x] Test all file endpoints for tenant isolation, authorization failures, and no disclosure of object-store credentials or internal paths.
- [x] Test delete and reprocess idempotency, including cleanup handoffs to document chunks and Qdrant.
- [x] Test knowledge-base association authorization and safe status/error responses.

## Definition of Done

- [x] Authorized tenants can upload, inspect, associate, reprocess, and delete supported files through the required endpoints.
- [x] Original files are stored under tenant-scoped MinIO keys and tracked by durable processing states.
- [x] File APIs and audit logs do not leak storage secrets, cross-tenant metadata, or internal errors.

## Suggested Day (1–4)

Day 3.
