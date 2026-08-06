# Planning Prompt — Multi-Tenant Text-to-SQL & Document Chat Platform

**How to use this:** Start a new session with your AI coding assistant (Claude Code, Cursor, or similar — it needs file-system access), attach the assignment PDF (`Text_to_SQL_and_Document_Chat_Assignment.pdf`) in that same session, then paste everything below the line as your message.

---

## Role

You are a senior backend/AI-systems architect with deep, hands-on expertise in multi-tenant SaaS backends, FastAPI, PostgreSQL + pgvector, LangGraph agent orchestration, retrieval-augmented generation, and SQL security hardening.

## Input

I've attached a PDF titled "Text-to-SQL and Document Chat Assignment." It specifies a backend system design assignment: a Multi-Tenant Text-to-SQL and Document Chat Platform. Read the entire document before doing anything else. Treat it as the single source of truth — don't invent requirements it doesn't contain, and don't soften, skip, or summarize away any requirement in it, especially the database schema (Section 7), the API list (Section 8), and the SQL security controls (Section 10).

## Goal

Don't write any implementation code in this task. Your only job right now is planning.

Produce the most complete, precise, and well-organized implementation plan possible for this whole project, split into small, sequential, numbered Markdown files, so the project can later be executed phase by phase — one file per focused work session.

## Hard constraints — never violate these

1. **One generic database agent — never one agent per table.** (Section 6) Never propose a fixed agent per table, tenant, or industry — only a single, reusable database agent that receives a request-specific, permission-filtered schema at runtime.
2. **Business data never leaves the source database.** (Section 17) The application database may only ever cache metadata, schema information, and small approved preview/sample values — never full customer records. Flag any task that would violate this.
3. **Read-only by default; destructive SQL is blocked.** (Section 10) `SELECT`/`WITH`/`EXPLAIN` are allowed by default; `DROP`/`TRUNCATE`/`ALTER`/`CREATE`/`GRANT`/`REVOKE`/`EXEC`/`CALL`/`COPY`/`ATTACH`/`DETACH` are blocked by default, multi-statements and SQL comments are blocked, and the LLM must never be able to create, remove, or modify a mandatory security filter.
4. **The Section 7 schema is a floor, not a ceiling.** Every table, column, constraint, and index specified there must exist exactly as written. Add extra tables/columns if genuinely needed, but never remove or rename what's already specified.
5. **Every Section 8 endpoint must exist, and the chat response must match Section 9's contract exactly** — field names `message_id`, `answer`, `intent`, `sources_used`, `sql.query_execution_id`, `sql.query`, `sql.row_count`, `citations[].type/file_name/page/table`.
6. **Environment setup mirrors the assignment exactly.** Phase `01` must scaffold the project tree from Section 4 (`app/`, `api/routes/`, `core/`, `models/`, `schemas/`, `repositories/`, `services/database/adapters/`, `services/documents/parsers/`, `services/chat/`, `services/llm/`, `agents/nodes/`, `agents/prompts/`, `storage/`, `vector_store/`, `workers/`, `migrations/`, `tests/`, `scripts/`, plus the root-level files) and the docker-compose services from Section 12 (`api`, `worker`, `postgres`, `redis`, `qdrant`, `minio`, `prometheus`, `grafana`) — unless you document a specific reason to deviate.

## Output location and format

1. Create a folder named exactly `plan` at the project root.
2. Inside it, create one Markdown file per phase, named with a zero-padded two-digit prefix and a short kebab-case slug, e.g. `plan/00-overview-and-roadmap.md`, `plan/01-environment-and-repo-setup.md`, `plan/02-database-schema-and-migrations.md`, and so on through the full phase list below.
3. The numeric prefix is the execution order: `00` is read first, then `01`, then `02`, etc. Never reuse a number, and don't leave a gap without explaining why in `00`.
4. Every file is clean, valid Markdown: headings, bullet lists, and `- [ ]` checkboxes for every actionable task, so progress can be tracked later by checking items off.
5. Create nothing outside `plan/`. No source code, no scaffolding yet — this pass is descriptions, decisions, and task checklists only.
6. If `plan/` already has files in it from an earlier run, don't silently overwrite them — list what's already there and ask before replacing anything.
7. If a real project already exists in the working directory (not just this PDF), skim its current structure first so the plan reflects what's actually there instead of assuming an empty repo.
8. If your AI tool can't create files directly (a chat-only assistant with no filesystem access), print each phase as a separate fenced code block headed by its filename (e.g. `plan/02-database-schema-and-migrations.md`) so the files can be saved manually.

## Required phases

Use this as the default breakdown. Merge, split, reorder, or rename phases only if it genuinely improves clarity, and only if the change is explained in `00` — coverage of every requirement in the PDF must stay at 100% either way.

- `00` Overview & Roadmap
- `01` Environment & Repository Setup
- `02` Application Database Schema & Migrations
- `03` Authentication & Tenant Context
- `04` Roles & Permission Model Foundations
- `05` Live Database Connections (CRUD, Encryption, Testing, Adapters)
- `06` Schema Discovery & Metadata Caching
- `07` Permission-Filtered Schema Resolution
- `08` Text-to-SQL Generation
- `09` SQL Validation & Safety Layer
- `10` Query Execution Engine
- `11` File Upload & Object Storage
- `12` Document Parsing & Chunking
- `13` Embeddings & Vector Store
- `14` Knowledge Base Management & Retrieval
- `15` Chat Orchestrator (LangGraph Agent Graph)
- `16` Conversation & Messaging Persistence
- `17` Citations & Traceability
- `18` Streaming Chat API (SSE)
- `19` Audit Logging & Observability
- `20` Security Hardening & Multi-Tenant Isolation Tests
- `21` Automated Testing Suite (Unit + Integration)
- `22` Documentation & Submission Packaging

## Template for phase files (01–22)

Every phase file contains exactly these sections, in this order:

```
# <Number>. <Phase Title>

## Goal
One paragraph: what this phase achieves and why it matters to the overall system.

## Depends On
Which earlier phase numbers must be finished first, and exactly what this phase needs from each.

## Assignment References
Which section(s) of the PDF this phase is derived from (e.g. "Section 7.3", "Section 10").

## Detailed Tasks
A granular, numbered `- [ ]` checklist — granular enough that someone could pick up only this file and implement the phase correctly without re-reading the whole PDF. Use exact table/column names, exact endpoint paths, exact config keys, and exact library choices wherever the PDF specifies them.

## Data Model Touched
Every Section 7 table/column this phase creates or modifies, if any.

## API Endpoints Touched
Every Section 8 endpoint this phase implements, if any.

## Security & Permission Notes
Anything from Section 10 or the permission model that applies here.

## Testing Requirements
What must be unit- or integration-tested before this phase counts as done (reference Sections 14 and 15).

## Definition of Done
A short, concrete, verifiable checklist for this phase.

## Suggested Day (1–4)
Which day of the assignment's four-day plan (Section 13) this phase best fits, for pacing.
```

### Example — the granularity "Detailed Tasks" should reach

For Phase `03` (Authentication & Tenant Context), tasks look like this — not "implement authentication":

```
- [ ] Create `models/user.py` matching the `users` table exactly (tenant_id FK, email, full_name, password_hash, status, is_tenant_admin, timestamps, unique (tenant_id, email))
- [ ] Implement password hashing (bcrypt/argon2) in `core/security.py`
- [ ] Implement JWT access + refresh token issuing and verification in `core/security.py`
- [ ] Build `POST /api/auth/login` — validates credentials scoped to the correct tenant, returns access + refresh tokens
- [ ] Build `POST /api/auth/refresh` — validates the refresh token, issues a new access token
- [ ] Build `GET /api/auth/me` — returns the current user plus resolved tenant and roles
- [ ] Add a `core/tenant_context.py` dependency that resolves `tenant_id` from the authenticated token on every request
```

## Template for `00-overview-and-roadmap.md`

This file is the entry point and must contain:

1. A one-paragraph summary of the whole system, in your own words.
2. The final ordered table of contents: every phase file with a one-line description.
3. A Day 1 / Day 2 / Day 3 / Day 4 mapping of phase numbers to days, matching or improving on Section 13.
4. A full **requirement traceability matrix** — one row per requirement drawn from Section 2 (Required System Capabilities), Section 8 (API list), Section 10 (SQL Security Controls), and Section 15 (Acceptance Criteria), with a column naming exactly which phase file(s) address it. No row may be left with an empty "owner" — if an unmapped requirement turns up, adjust a phase until it's covered.
5. A list of every open technical decision where the PDF offers a choice (e.g. Celery vs. Dramatiq, pgvector vs. Qdrant, MinIO vs. S3 vs. Azure Blob) — a default recommendation and a one-line reason for each, clearly flagged **"DECISION NEEDED — confirm before Phase X"** for confirmation or override before implementation starts.
6. A short "Individual Work" note as a reminder to record in the README which tools — including any AI assistant — were used, per the assignment's Section 16.

## Quality bar

- Cross-check the finished plan against every one of Sections 2–15 before stopping. Every table, column, endpoint, security rule, and acceptance criterion in the PDF must map to at least one task in one phase file — fix any gap found.
- Stay faithful to the Section 11 stack (FastAPI, PostgreSQL + SQLAlchemy 2/Alembic, LangGraph, Celery or Dramatiq, Redis, pgvector or Qdrant, MinIO/S3/Azure Blob, SQLGlot, Docling, SSE, Prometheus/Grafana/OpenTelemetry) unless there's a specific reason to deviate — and if so, say why.
- No vague tasks like "implement authentication" — break everything down into which endpoints, which tables, which middleware, which token type, which error responses.
- Read the whole PDF end-to-end and mentally build the dependency graph between phases before writing anything; then write `00`, then `01`, `02`, … in order.
- Write everything in English.

## When you finish

Give a short chat summary: how many phase files were created, and every "DECISION NEEDED" flag that needs confirmation before implementation begins.
