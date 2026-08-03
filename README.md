# Multi-Tenant Text-to-SQL & Document Chat Platform

An enterprise-grade, multi-tenant platform combining read-only Text-to-SQL query generation against live databases with Retrieval-Augmented Generation (RAG) over structured knowledge-base documents.

Built with **FastAPI**, **SQLAlchemy 2**, **Alembic**, **SQLGlot AST Validator**, **Qdrant Vector Store**, **PostgreSQL (pgvector)**, **MinIO Object Storage**, **Redis**, **Celery**, and **LangGraph**.

---

## Key Features

- **Multi-Tenant Isolation & Authentication**: Strict tenant-scoped data isolation enforced at repository, database, vector-store, and storage layers. Argon2id password hashing and PyJWT access/refresh token rotation.
- **Role & Permission Model Foundations**: Tenant-scoped Role Management, Table/Column permission grants with direct-user grant precedence over role grants, column projection/filter/aggregate gates, and sensitivity masking (`redact`, `last4`, `hash`).
- **Live Database Connection & Introspection**: Encrypted database connection credentials (bound to tenant context AAD), SSRF host validation, live PostgreSQL schema introspection, and automated schema metadata sync.
- **Permission-Filtered Schema Resolution**: Dynamic, request-specific short-lived schema resolution including server-side AST compiled JSON DSL row-filter injection (`tenant_id` and `user_id` context placeholders).
- **Text-to-SQL & AST Safety Layer**: SQLGlot AST parsing enforcing strict read-only queries (`SELECT`, `WITH ... SELECT`, `UNION SELECT`), rejection of DDL/DML (`INSERT`, `UPDATE`, `DELETE`, `DROP`), AST row-filter injection into `WHERE` clauses, limit clamping (max 1,000 rows), and statement timeouts.
- **Bounded Query Execution Engine**: Safe read-only connection pool execution, column sensitivity masking, transient result envelopes, and sanitized `query_executions` audit record persistence.
- **Tenant-Scoped Object & File Storage**: Multi-format document upload (PDF, Word `.docx`, Excel `.xlsx`, CSV, Text) under tenant-isolated paths using unguessable prefixes, SHA-256 checksums, and durable processing status in PostgreSQL.
- **Format-Specific Parsing & Deterministic Chunking**: Text extraction, SHA-256 content hashes, chunk indexing, page/section provenance tracking, and document chunks persistence.
- **1024-Dimension Vector Store Indexing**: 1024-dimension float vector embedding generation (`EmbeddingService`), vector dimension validation, Qdrant vector store indexing with mandatory tenant and knowledge-base payload filters, and pgvector mirror updates.
- **Knowledge Base Management & RAG Retrieval**: Tenant KB CRUD endpoints, document evidence retrieval, vector search, and citation-ready provenance formatting.
- **Unified Chat Orchestrator (LangGraph Agent Graph)**: Single reusable chat graph classifying requests into 5 intents (`general`, `database`, `document`, `hybrid`, `clarification`), coordinating SQL execution, RAG document retrieval, and grounded final answer synthesis.
- **Conversation & Message Persistence**: Session management (`conversations` and `messages` tables) tracking question prompts, assistant answers, latency, and intent.
- **Durable Citations & Traceability**: `MessageCitation` persistence linking assistant responses back to document chunks or SQL query executions, served via `GET /api/messages/{id}/citations` and `GET /api/messages/{id}/sql`.
- **Streaming SSE Chat API**: Server-Sent Events interface (`POST /api/chat/stream`) emitting structured event framing sequences (`intent`, `answer`, `done`) adhering to Section 9 response contract compatibility.
- **Structured Audit Logging & Observability**: Tenant-aware audit logging (`audit_logs` table) with automatic credential/secret redaction (`password`, `token`, `secret`) and operational health probes (`GET /api/health`).
- **Security Hardening & Automated Test Suite**: Comprehensive security regression suite asserting 100% multi-tenant isolation, SQL injection hardening, sensitive data masking, Section 8 API contract verification, and 81 passing tests across all 21 phases.

---

## Architecture Overview

```
                        +--------------------------------+
                        |   Client Application / REST    |
                        +---------------+----------------+
                                        |
                                        v
                        +---------------+----------------+
                        |  FastAPI Router & Auth Middleware|
                        +---------------+----------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                       LangGraph Chat Orchestrator                             |
|                                                                               |
|   +-------------------+   +--------------------+   +-----------------------+  |
|   | Intent Classifier |-->| Database SQL Agent |-->| AST Validator (SQLGlot)| |
|   +-------------------+   +--------------------+   +-----------+-----------+  |
|             |                                                  |              |
|             v                                                  v              |
|   +-------------------+                            +-----------+-----------+  |
|   | Document RAG Agent|                            | Query Execution Engine|  |
|   +---------+---------+                            +-----------+-----------+  |
+-------------|--------------------------------------------------|--------------+
              |                                                  |
              v                                                  v
+-------------+-----------+                         +------------+------------+
| Qdrant Vector Store     |                         | Customer Database (Live)|
| (Tenant-Scoped Payloads)|                         | (Read-Only Connection)  |
+-------------------------+                         +-------------------------+
              |                                                  |
              v                                                  v
+-------------+--------------------------------------------------+------------+
|                  Platform PostgreSQL DB (Alembic Schema)                    |
| (tenants, users, roles, connections, files, document_chunks, conversations, |
|           messages, query_executions, citations, audit_logs)                |
+-----------------------------------------------------------------------------+
```

---

## Prerequisites

- **Python**: `3.11+`
- **PostgreSQL**: `15+` (with `pgvector` extension)
- **Redis**: `7.0+`
- **Qdrant**: `1.7+`
- **Docker Compose** (for running infrastructure)

---

## Environment Setup

1. **Clone Repository & Setup Environment**:
   ```bash
   git clone <repository-url>
   cd "ITI Project"
   cp .env.example .env
   ```

2. **Install Python Dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r pyproject.toml
   ```

3. **Start Infrastructure Services (Docker Compose)**:
   ```bash
   docker-compose up -d
   ```

4. **Apply Database Migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Seed Database Admin Account**:
   ```bash
   python scripts/seed_admin.py
   ```

---

## Running the Application

1. **Start FastAPI Application Server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Open Swagger UI documentation at: [http://localhost:8000/docs](http://localhost:8000/docs)

2. **Start Celery Worker (Background File & Embedding Jobs)**:
   ```bash
   celery -A worker.celery_app worker --loglevel=info
   ```

---

## Running the Automated Test Suite

Run the full test suite using `pytest`:

```bash
pytest
```

Output:
```bash
============================= 81 passed in 4.19s ==============================
```

---

## API Endpoints Reference (Section 8)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Overall system operational health check |
| `POST` | `/api/auth/login` | Authenticate user and issue PyJWT token pair |
| `POST` | `/api/auth/refresh` | Refresh access token using refresh token |
| `GET` | `/api/auth/me` | Get current authenticated user context |
| `POST` | `/api/database-connections` | Create a new tenant database connection |
| `GET` | `/api/database-connections` | List tenant database connections |
| `GET` | `/api/database-connections/{id}` | Get connection details (redacted secrets) |
| `POST` | `/api/database-connections/{id}/test` | Test read-only connection probe (`SELECT 1`) |
| `POST` | `/api/database-connections/{id}/sync-schema` | Introspect and sync database schema metadata |
| `POST` | `/api/files/upload` | Upload document file (PDF, Word, Excel, CSV, Text) |
| `GET` | `/api/files` | List tenant uploaded files |
| `GET` | `/api/files/{id}` | Get file metadata details |
| `DELETE` | `/api/files/{id}` | Delete file metadata and storage object |
| `POST` | `/api/files/{id}/reprocess` | Reset file status to pending for reprocessing |
| `POST` | `/api/knowledge-bases` | Create a new tenant knowledge base |
| `GET` | `/api/knowledge-bases` | List tenant knowledge bases |
| `POST` | `/api/knowledge-bases/{id}/files` | Associate file with a knowledge base |
| `POST` | `/api/conversations` | Create a new conversation session |
| `GET` | `/api/conversations` | List tenant conversations |
| `GET` | `/api/conversations/{id}` | Get conversation metadata & message history |
| `DELETE` | `/api/conversations/{id}` | Delete conversation and messages |
| `POST` | `/api/chat` | Synchronous chat orchestrator pipeline |
| `POST` | `/api/chat/stream` | Streaming SSE chat orchestrator endpoint |
| `GET` | `/api/messages/{id}/citations` | Get source citations for a message |
| `GET` | `/api/messages/{id}/sql` | Get SQL execution trace for a database message |

---

## Documented Baseline Assumptions

1. **Celery / Redis Worker Baseline**: Used for asynchronous background task execution, file ingestion, chunking, and embedding synchronization.
2. **Qdrant + PostgreSQL Vector Mirror**: Qdrant serves as the canonical vector store for RAG similarity search, while PostgreSQL `document_chunks.embedding` retains the `Vector(1024)` representation.
3. **1024-Dimension Embedding Model**: Standardized on 1024-dimension float vectors (`bge-large-en-v1.5` baseline) with strict L2-normalization and dimension validation.
4. **Local / MinIO Storage Baseline**: Files are stored under tenant-isolated local paths (`storage/{tenant_id}/{stored_name}`) with SHA-256 checksums.
5. **SSE Streaming Event Sequence**: `POST /api/chat/stream` emits structured events: `intent`, `answer`, and `done` (containing complete `ChatResponse` JSON payload for 100% Section 9 contract compatibility).

---

## AI & External Tool Disclosure (Section 16)

As required by Section 16 of the project specifications, all work in this repository was completed independently. AI coding assistants (including Antigravity AI) were used for pair programming, code generation, refactoring, test suite assembly, and documentation generation under developer guidance and supervision.

---

## License

MIT License. See LICENSE file for details.
