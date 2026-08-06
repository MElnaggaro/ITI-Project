# System Architecture & Component Design

## Overview

The platform is an enterprise-grade multi-tenant system combining **Read-Only Text-to-SQL Query Generation** over live databases with **Retrieval-Augmented Generation (RAG)** over knowledge documents.

---

## High-Level Architecture Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                  CLIENT LAYER (Frontend UI / REST / SSE)                          |
|                       Modern Glassmorphic HTML5 / JS (EventSource Streaming)                      |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                              FASTAPI API GATEWAY & SECURITY LAYER                                 |
|         Authentication (PyJWT / Argon2id) | Tenant Context Binding | Fernet Encryption            |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                              LANGGRAPH UNIFIED CHAT ORCHESTRATOR                                  |
|                                                                                                   |
|  +-------------------+       +-------------------------+       +------------------------------+   |
|  | Intent Classifier | ----> | Database SQL Agent Node | ----> | SQLGlot AST Safety Validator |   |
|  | (general/db/doc/  |       | (qwen3.5:4b Local LLM)  |       | (Read-only, Permission Check |   |
|  |  hybrid)          |       +-------------------------+       |  & AST Row-Filter Injection) |   |
|  +---------+---------+                                         +--------------+---------------+   |
|            |                                                                  |                   |
|            v                                                                  v                   |
|  +-------------------+                                         +--------------+---------------+   |
|  | Document RAG Agent|                                         | Bounded Execution Engine     |   |
|  | (Qdrant Vector DB)|                                         | (Postgres/MySQL/Oracle/MSSQL)|   |
|  +---------+---------+                                         +--------------+---------------+   |
|            |                                                                  |                   |
|            +----------------------------+-------------------------------------+                   |
|                                         |                                                         |
|                                         v                                                         |
|                              +----------+--------------+                                          |
|                              |    Hybrid Merger Node   |                                          |
|                              +-------------------------+                                          |
+-----------------------------------------+---------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------+---------------------------------------------------------+
|                                DATA & STORAGE PERSISTENCE LAYER                                   |
|   Platform PostgreSQL 16 (pgvector) | Qdrant Vector Store (1024-dim) | MinIO Object Storage      |
+-----------------------------------------+---------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------+---------------------------------------------------------+
|                               ASYNCHRONOUS WORKER & OBSERVABILITY                                 |
|            Celery Background Workers + Redis | Prometheus Metrics & Grafana Dashboards              |
+---------------------------------------------------------------------------------------------------+
```

---

## Detailed Component Breakdown

### 1. Client & API Gateway Layer
- **Frontend Dashboard**: Single-page web application (`frontend/index.html`, `app.js`, `style.css`) consuming FastAPI endpoints and processing real-time Server-Sent Events (`POST /api/chat/stream`).
- **Security Middleware**: Authenticates user requests via PyJWT tokens, resolves immutable `TenantContext(tenant_id, user_id)`, and decrypts source connection passwords using Fernet symmetric encryption bound to tenant context.

### 2. LangGraph Unified Chat Orchestrator
The chat engine operates as a state machine (`ChatOrchestrator`) defined using **LangGraph**:
1. **Intent Classifier Node**: Analyzes incoming prompts and assigns routing intent (`general`, `database`, `document`, or `hybrid`).
2. **Source Selector Node**: Filters accessible database connections and knowledge bases against user permissions.
3. **Database SQL Agent Node**: Uses local Ollama LLM (`qwen3.5:4b`) to generate candidate SQL statements strictly against the user's `ResolvedSchema`.
4. **Document Agent Node (RAG)**: Generates 1024-dimension float vector embeddings (`bge-large-en-v1.5` / FastEmbed / Ollama), retrieves top-k relevant document chunks from **Qdrant**, applying mandatory `tenant_id` and `knowledge_base_id` payload filters.
5. **Hybrid Merger Node**: Combines database query result preview data with document evidence citations into a coherent unified response.
6. **Final Response Node**: Persists conversation history, messages, and `MessageCitation` provenance records, emitting structured SSE events (`intent`, `answer`, `done`).

### 3. SQLGlot AST Safety & Validation Engine
Before any candidate SQL touches a target database, it passes through the **SQLGlot AST Safety Layer**:
- **AST Parsing**: Parses SQL into dialect-specific Abstract Syntax Trees.
- **Statement Type Filtering**: Enforces read-only statements (`SELECT`, `WITH ... SELECT`, `UNION SELECT`) and rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, procedure calls, and comments.
- **Permission Verification**: Validates that all referenced tables and columns are explicitly permitted for the user.
- **Row-Filter AST Injection**: Compiles JSON DSL row filters into SQLGlot AST expressions (e.g. `WHERE tenant_id = '...'`) and injects them directly into the query AST.
- **Limit Clamping**: Automatically injects or clamps `LIMIT` clauses to a maximum of 1,000 rows.

### 4. Bounded Query Execution Engine
- Connects to target read-only customer databases (**PostgreSQL**, **MySQL**, **SQL Server**, **Oracle**).
- Applies column sensitivity masking rules (`redact` -> `[REDACTED]`, `last4` -> `***************9012`, `hash`).
- Persists sanitized execution records to the `query_executions` audit table.

### 5. Data & Storage Persistence
- **Platform PostgreSQL 16**: Relational storage for tenants, users, roles, permissions, database catalog cache, files, conversations, messages, citations, and audit logs. Uses `pgvector` for vector mirroring.
- **Qdrant Vector Store**: Dedicated vector database storing 1024-dimension document embeddings with payload filtering.
- **MinIO / Local Object Storage**: Tenant-isolated file storage using unguessable storage paths and SHA-256 checksums.

### 6. Background Workers & Observability
- **Celery Workers + Redis**: Handles asynchronous schema sync (`sync_schema_task`) and document pipeline processing (`process_document_task`: text extraction, chunking, embedding, vector indexing).
- **Prometheus & Grafana**: Collects system metrics and renders operational health dashboards.
