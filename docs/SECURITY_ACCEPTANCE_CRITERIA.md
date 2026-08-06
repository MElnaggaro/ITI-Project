# Security Acceptance Criteria & Multi-Tenant Isolation Specifications

This document defines the strict, non-ambiguous, and fully testable **Security Acceptance Criteria** for the **Text-to-SQL and Document Chat (RAG)** platform.

---

## Executive Security Architecture

```
                                    ┌────────────────────────────────────────┐
                                    │               Client API               │
                                    └───────────────────┬────────────────────┘
                                                        │ JWT Authentication & Tenant Context
                                                        ▼
                                    ┌────────────────────────────────────────┐
                                    │         Backend Gateway (FastAPI)       │
                                    └───────────────────┬────────────────────┘
                                                        │ Candidate SQL / Query Intent
                                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SECURITY & AUTHORIZATION BOUNDARY                                    │
│                                                                                                        │
│  ┌─────────────────────────────────┐   ┌────────────────────────────────┐   ┌───────────────────────┐  │
│  │   AST Read-Only Verification    │   │  Backend Tenant Filter Rewrite  │   │  Limit Clamping & DoS │  │
│  │   - Reject DDL/DML/Multi-stmt   │   │  - Inject WHERE tenant_id=X    │   │  - Max LIMIT 100      │  │
│  │   - Block system catalogs       │   │  - Parameterized bindings      │   │  - Timeout <= 5s      │  │
│  └─────────────────────────────────┘   └────────────────────────────────┘   └───────────────────────┘  │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Sanitized Executable Plan
                                                    ▼
                                    ┌────────────────────────────────────────┐
                                    │    Target Database / Vector Store      │
                                    └────────────────────────────────────────┘
```

> [!IMPORTANT]
> **LLM Zero-Trust Policy:** The LLM is treated as an untrusted candidate SQL/text generator. Neither tenant isolation filters, row limits, database credentials, nor authorization decisions are delegated to the LLM. All access controls are hard-enforced by backend AST rewriting and API middleware prior to execution.

---

## 1. Security Acceptance Criteria Table

| Domain | Capability | Required Behavior | Expected Result | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Multi-Tenant Isolation** | Text-to-SQL Tenant Scoping | The backend inspects candidate SQL via `sqlglot` AST parser and forcibly injects `tenant_id` equality filters into every base table and join clause using server-owned parameters. | Cross-tenant data retrieval is impossible, even if requested directly in prompt or written into LLM candidate SQL. | Automated Unit & Integration Tests (`test_multi_tenant_isolation.py`) |
| **Multi-Tenant Isolation** | RAG / Vector Store Scoping | All similarity searches in vector store (Qdrant/PgVector) strictly enforce a mandatory `tenant_id` metadata payload filter extracted directly from verified JWT claims. | Embeddings retrieval yields zero document chunks belonging to other tenants. | Unit & Integration Vector Search Tests |
| **SQL Safety** | Read-Only Statement Verification | AST parser recursively verifies that candidate query contains ONLY `SELECT` operations. All DML/DDL (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`), CTE write variants, and procedural executions are rejected. | Any non-read-only statement is rejected immediately with HTTP `400 Bad Request` / `403 Forbidden` prior to execution. | AST Validation Unit Tests (`test_sql_safety.py`) |
| **SQL Safety** | Multi-Statement & Comment Defense | Reject candidate queries containing statement terminators (`;`), SQL comments (`--`, `/* */`), or unparseable dialect syntax. | Multi-statement execution or injection via SQL comments is prevented. | Parser Safety Tests |
| **SQL Safety** | System Schema & Catalog Isolation | Queries referencing system catalogs (`pg_catalog`, `information_schema`, `sys.tables`, `sqlite_master`) or administrative functions are blocked. | Database schema internals and administrative metadata are hidden from LLM and end-users. | Catalog Rejection Tests |
| **DoS Defense** | Result Limit Clamping | Mandatory result limit (max 100 rows) is injected into AST. Existing smaller limits are preserved, while larger or missing limits are clamped. | Query result sizes are bounded; memory overflow and payload bloat are avoided. | Limit Rewriting Tests |
| **DoS Defense** | Query Execution Timeout | Source database queries execute under a hard statement timeout ($\le 5$ seconds). | Cartesian joins and heavy queries are auto-terminated before causing database instability. | Timeout Execution Tests |
| **Prompt Security** | Injection & Jailbreak Guardrails | Input prompts undergo sanitization against direct/indirect prompt injection (e.g., "Ignore previous instructions", "Dump all tables"). | System prompts and tenant boundaries remain intact regardless of user input manipulation. | Prompt Injection Test Suite |
| **Audit & Traceability** | Sanitized Audit Logging | Every query execution records tenant ID, user ID, normalized SQL, execution duration, and status. Credentials and raw PII parameters are stripped. | Complete forensic audit trail is maintained without leaking sensitive data or database secrets. | Audit Log Repository Tests |

---

## 2. Detailed Technical Requirements

### 2.1 Text-to-SQL AST Validation Pipeline
1. **Parsing:** Candidate SQL must parse successfully using `sqlglot` under the target database dialect (PostgreSQL, MySQL, SQLite).
2. **Recursive AST Traversal:** 
   - Root expression must be `exp.Select` or `exp.Union` / `exp.Expression`.
   - Iterate all child nodes: reject any node of type `exp.Insert`, `exp.Update`, `exp.Delete`, `exp.Drop`, `exp.Create`, `exp.Alter`, `exp.Truncate`, `exp.Command`.
3. **Table & Column Authorization:**
   - Resolve all referenced base tables against tenant schema permissions.
   - Expand wildcards (`SELECT *`) to explicit permitted column lists.
   - Reject queries referencing unpermitted or masked columns.
4. **Tenant Predicate & Parameter Binding:**
   - Inject `WHERE tenant_id = :tenant_id` (or appropriate join predicate) into every table reference.
   - Bind parameters separately using parameterized execution engine (`SQLAlchemy` text with bound parameters).

### 2.2 Vector Search Metadata Enforcement
1. **Filter Assembly:**
   ```json
   {
     "must": [
       { "key": "tenant_id", "match": { "value": "<authenticated_tenant_id>" } },
       { "key": "is_active", "match": { "value": true } }
     ]
   }
   ```
2. **Payload Validation:** Vector query engine must reject search requests missing verified `tenant_id` context.

---

## 3. Definition of Done (DoD) for Security

- [x] All 9 security capabilities in the criteria table are backed by automated tests in `backend/tests/security/`.
- [x] Zero raw/unbound user or LLM strings are concatenated into live database queries.
- [x] All multi-tenant isolation tests pass cleanly in continuous integration.
