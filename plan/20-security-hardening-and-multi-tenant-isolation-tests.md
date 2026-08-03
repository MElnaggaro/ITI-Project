# 20. Security Hardening and Multi-Tenant Isolation Tests

## Goal

Prove the platform enforces tenant, role, table, column, row, document, and SQL safety boundaries before submission, with special attention to hostile requests that try to exploit LLM output, identifiers, source connections, storage, or background jobs.

## Depends On

- [ ] Phases 03 and 04 provide authentication, tenant context, roles, permissions, masking, and row-filter policy.
- [ ] Phases 05 through 10 provide connection security, schema filtering, SQL generation, validation, and execution controls.
- [ ] Phases 11 through 19 provide storage isolation, document access controls, chat, persistence, streaming, audit, and observability.
- [ ] Phase 21 supplies shared test infrastructure and fixtures.

## Assignment References

- [ ] Sections 2, 5, 6, 7.5, 8, 10, 14, 15, 16, and 17.

## Detailed Tasks

- [ ] Build a threat-model checklist covering API authentication, tenant/resource ID substitution, role escalation, table/column/row disclosure, SQL injection/escape attempts, source connection misuse, file/object access, vector retrieval leakage, worker context loss, streaming leakage, and audit/log leakage.
- [ ] Define two or more isolated tenant fixtures with separate users, roles, connections, schemas, knowledge bases, files, conversations, chunks, citations, query executions, object prefixes, Qdrant payloads, and jobs.
- [ ] Test every public resource endpoint rejects a valid resource ID owned by another tenant with a safe not-found/forbidden result.
- [ ] Test tenant context cannot be overridden with request body fields, headers, query parameters, conversation settings, graph state, or worker payloads.
- [ ] Test table permissions deny ungranted tables, column permissions deny/unmask prohibited columns, and sensitive-column policies hold in filtered schemas, prompts, SQL, results, logs, citations, and final answers.
- [ ] Test row filters are compiled server-side, parameterized, conjuncted with mandatory predicates, preserved through aliases/subqueries, and cannot be removed, widened, or replaced by generated SQL.
- [ ] Test direct-user and role permission precedence against the documented Phase 00 baseline, including no-grant, conflicting-grant, invalid-filter, and explicit-unrestricted-scope cases.
- [ ] Test SQLGlot validation rejects comments, multi-statements, DDL, destructive DML, blocked commands, write CTEs, SELECT INTO, locking/write clauses, system schemas, administrative functions, disallowed dialect features, and EXPLAIN over unsafe statements.
- [ ] Test SQL validation enforces read-only source credentials, query row/result limits, timeouts, identifier allow-lists, masked values, and safe query-execution auditing.
- [ ] Test only the reusable generic database agent receives a filtered runtime schema; assert no per-table agent configuration or prompt exists.
- [ ] Test connection creation/test/update hides encrypted credentials and blocks unauthorized users, unsafe host/network targets according to deployment policy, and secret-bearing error messages.
- [ ] Test tenant-qualified object paths, signed/object access, Qdrant filters, Redis keys, Celery payload context, and cache entries prevent cross-tenant file/chunk retrieval.
- [ ] Test document file types, parser failures, reprocessing, deletion, and citations do not leak content or metadata across tenant/knowledge-base boundaries.
- [ ] Test general, database, document, hybrid, and streaming responses redact internal errors, credentials, excluded schema, raw restricted rows, and hidden chunks.
- [ ] Test audit logs, metrics labels, traces, query previews, and exception responses do not persist or expose forbidden business data or secrets.
- [ ] Record each security test's assignment control and acceptance criterion in a traceability table for submission evidence.

## Data Model Touched

- [ ] Tenant-scoped access is verified across all Section 7 tables, especially table_permissions, column_permissions, database metadata, files, document_chunks, conversations, messages, query_executions, message_citations, and audit_logs.

## API Endpoints Touched

- [ ] All Section 8 endpoints are exercised for authentication, authorization, tenant isolation, and safe failure behavior.

## Security & Permission Notes

- [ ] This phase treats every user-controlled identifier, LLM output, uploaded file, source connection attribute, and asynchronous job payload as untrusted.
- [ ] Security tests must demonstrate rejection before unsafe SQL reaches a source database and before a cross-tenant resource is read.

## Testing Requirements

- [ ] Execute the full security regression suite against isolated test tenants and a read-only source database fixture.
- [ ] Include negative tests for every mandatory Section 10 control and every Section 15 isolation/reliability criterion.
- [ ] Ensure failed assertions retain no real credentials or customer data in artifacts.

## Definition of Done

- [ ] Security evidence proves unauthorized tables, columns, rows, tenants, and destructive SQL are blocked.
- [ ] Source business data is not bulk-copied into platform persistence, logs, or vector search.
- [ ] Failures are safe, observable, and non-disclosing.

## Suggested Day (1–4)

Day 4
