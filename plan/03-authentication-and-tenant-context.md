# 03. Authentication and Tenant Context

## Goal

Establish a secure FastAPI authentication boundary that derives one trusted tenant and user context from every authenticated request. Authentication must support the required login, refresh, and identity endpoints without ever trusting a client-supplied tenant ID for authorization or data access.

## Depends On

- [x] Phase 01 provides configuration, dependency-injection, exception, logging, and Redis service boundaries.
- [x] Phase 02 preserves the Section 7 `tenants` and `users` DDL and exposes tenant-scoped repositories.

## Assignment References

- [x] Sections 1, 2, 3, 4, 5 steps 1–2, 7.1, 8, 10, 11, 13, 14, 15, and 17.

## Detailed Tasks

- [x] Define FastAPI request dependencies that authenticate a bearer token, validate its issuer, audience, signature, expiration, token type, and token identifier, then construct an immutable `TenantContext` containing only trusted `tenant_id`, `user_id`, request ID, and tenant-admin flag.
- [x] Use the selected baseline authentication design—short-lived JWT access tokens plus rotating refresh tokens, Argon2id password hashes, and Redis-backed refresh-token identifiers/revocation state—and label it as a **Baseline assumption**, not a Section 8 wire-contract requirement.
- [x] Define the **Baseline assumption** login request as `tenant_code`, `email`, and `password`; use `tenant_code` only to locate the login tenant before authentication, never as an authorization input after a token is issued.
- [x] Define access-token claims as a minimally sufficient signed identity set: subject/user ID, tenant ID, token type, issued/expiry times, and token ID; resolve current roles and permissions from tenant-scoped storage rather than trusting role grants embedded in a stale token.
- [x] Implement the planned `POST /api/auth/login` flow: look up the tenant by unique code, load the user through `(tenant_id, email)`, require active tenant and user statuses, verify the Argon2id hash in constant-time-compatible library code, issue an access/refresh pair, and emit a safe audit event.
- [x] Return the same non-enumerating authentication failure for unknown tenant, unknown email, disabled account, disabled tenant, invalid password, expired refresh token, and revoked refresh token; do not disclose which condition failed.
- [x] Implement the planned `POST /api/auth/refresh` flow: require a valid refresh-token type and Redis token identifier, rotate it atomically into a new token pair, revoke the prior identifier, and reject replay, expiration, tenant/user status changes, and missing state without revealing internals.
- [x] Implement the planned `GET /api/auth/me` flow using only `TenantContext`; return safe identity and current tenant information needed by the client, never `password_hash`, token material, internal status diagnostics, or another tenant's data.
- [x] Check current tenant and user active status on each authenticated request or a safely invalidated equivalent, so disabling either principal takes effect before protected service work begins.
- [x] Make every repository and service entry point that reads tenant-owned data require `TenantContext` (or an equivalent trusted tenant/user pair); prohibit unscoped lookup-by-ID methods for externally reachable resources.
- [x] Add a dependency that attaches a request correlation ID and authenticated context to structured logs and audits while redacting Authorization headers, passwords, tokens, refresh identifiers, and any connection credentials.
- [x] Apply login and refresh rate limits keyed by a privacy-safe combination of tenant selector, account selector, and source address; return generic throttling responses and audit the security event without storing plaintext credentials.
- [x] Define bootstrap/provisioning of the first tenant administrator as deployment or migration seeding rather than inventing an unrequired public tenant/user-management endpoint.
- [x] Document that `is_tenant_admin` authorizes tenant administration such as connection and permission management, but does not automatically bypass table, column, row, masking, or source-database controls used by chat.
- [x] Publish a narrow authentication-service interface for later phases: `require_context`, `require_tenant_admin`, and tenant-scoped repository helpers; do not let LangGraph, an LLM, or client JSON manufacture this context.

## Data Model Touched

- [x] Preserve `tenants` exactly as Section 7.1 specifies: UUID primary key with `uuid_generate_v4()` default; non-null `name`; unique non-null `code`; non-null `status` defaulting to `active`; non-null `settings JSONB` defaulting to `{}`; and non-null creation/update timestamps defaulting to `NOW()`.
- [x] Preserve `users` exactly as Section 7.1 specifies: UUID primary key default; `tenant_id` non-null foreign key to `tenants(id)` with `ON DELETE CASCADE`; tenant-scoped unique email constraint; nullable `full_name` and `password_hash`; non-null `status` defaulting to `active`; non-null `is_tenant_admin` defaulting to `FALSE`; timestamps; and `idx_users_tenant_id`.
- [x] Keep refresh-token rotation and revocation identifiers in Redis with expiry rather than persisting raw refresh tokens or adding an unapproved source-data table; store only opaque identifiers and safe lifecycle metadata.
- [x] Read `roles` and `user_roles` only through tenant-scoped joins when producing the safe current-user view; Phase 04 owns their mutation and authorization semantics.
- [x] Write authentication audit events through the future `audit_logs` interface without placing secrets, token contents, or password-verification details in `details`.

## API Endpoints Touched

- [x] Implement the required `POST /api/auth/login` endpoint with the baseline login request described above and a safe token-pair response.
- [x] Implement the required `POST /api/auth/refresh` endpoint with a refresh token input and rotated safe token-pair response.
- [x] Implement the required `GET /api/auth/me` endpoint using the bearer token only; it accepts no client-supplied tenant identifier.
- [x] Do not add a public tenant/user provisioning endpoint as though it were required by Section 8; any future administration surface must be documented separately as a baseline extension.

## Security & Permission Notes

- [x] Treat the JWT's verified tenant and user claims as the sole request identity source; reject a request if body, path, query, or selected-resource data attempts to substitute another tenant context.
- [x] Enforce tenant predicates in application-database repositories, worker payloads, cache keys, object keys, vector filters, and resource lookups; later phases must receive the context rather than independently accepting tenant IDs.
- [x] Keep access and refresh signing/encryption configuration outside source control, validate required secret settings at startup, and never expose them through OpenAPI examples, errors, logs, or audits.
- [x] Use generic authorization failures for cross-tenant or unauthorized resource IDs so callers cannot enumerate tenants, users, connections, metadata, conversations, or files.
- [x] Make authentication failure terminal before schema discovery, permission resolution, source-database access, document retrieval, or chat orchestration begins.

## Testing Requirements

- [x] Unit-test password hashing and verification, access-token validation, token-type separation, expiration, signature failure, refresh rotation, replay rejection, and revoked-token rejection.
- [x] Integration-test login and `/me` for active users, inactive users, inactive tenants, incorrect tenant codes, wrong passwords, and rate-limit behavior using indistinguishable unsafe-login responses.
- [x] Test that changing a tenant/user status prevents subsequent access and refresh before protected endpoints perform database work.
- [x] Test that a valid token for tenant A cannot access a tenant-B resource even when the request body, URL, or selected ID names tenant B.
- [x] Test that logs, audit payloads, validation errors, and API responses never contain passwords, password hashes, bearer tokens, refresh tokens, or connection secrets.

## Definition of Done

- [x] All three required authentication endpoints authenticate safely and produce/consume the documented baseline token lifecycle.
- [x] Every protected route can obtain one immutable trusted tenant/user context and cannot authorize from a client-supplied tenant ID.
- [x] Tenant administration is distinguishable from source-data access; tenant admins still require explicit data permissions for chat.
- [x] Authentication errors are safe, rate-limited, auditable, and free of secrets or internal stack traces.

## Suggested Day (1–4)

Day 1
