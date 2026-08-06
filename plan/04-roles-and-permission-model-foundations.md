# 04. Roles and Permission Model Foundations

## Goal

Establish tenant-scoped roles, direct-user grants, table/column permissions, masking policy, and a fail-closed permission-management foundation. The model must supply one unambiguous policy source for the permission-filtered schema and SQL safety phases while keeping management interfaces explicitly separate from the Section 8 required API list.

## Depends On

- [x] Phase 02 preserves the required `roles`, `user_roles`, `table_permissions`, and `column_permissions` DDL and supplies migrations/repositories.
- [x] Phase 03 provides trusted `TenantContext` and the tenant-admin authorization dependency.
- [x] Phase 05 provides tenant-scoped database connections, and Phase 06 provides discovered schemas, tables, and columns to which grants can refer.

## Assignment References

- [x] Sections 1, 2, 3, 4, 5 step 4, 7.2, 7.5, 10 controls 1, 7, 8, 9, and 12, 13, 14, 15, and 17.

## Detailed Tasks

- [x] Model tenant roles as named tenant-local groups and user-role assignments; never resolve a role, user, connection, table, or column by ID without confirming that it belongs to the active tenant.
- [x] Preserve the required exclusive permission subject model: every `table_permissions` row names exactly one role or one user, enforced by `chk_permission_subject`; reject API requests that name both or neither subject.
- [x] Add a documented **Baseline extension** migration for one direct-user grant per `(user_id, connection_id, table_id)` and one role grant per `(role_id, connection_id, table_id)` using partial unique indexes. This preserves the Section 7 core DDL while preventing ambiguous precedence records.
- [x] Define fail-closed defaults at the service layer: absent table grant means no table access; absent column grant means no column access; a disabled table, inactive connection, or inactive tenant means no chat exposure regardless of a stored grant.
- [x] Define the direct-user precedence rule: if a direct-user table permission exists for a user, it is the sole effective table grant for that user/connection/table; `can_read = false` is an explicit denial and role grants do not widen it. If no direct grant exists, the user's role grants are additive for that table.
- [x] Define role aggregation rule: when no direct grant exists, any role grant with `can_read = true` grants read access, and the effective row predicate is the parenthesized OR of those read-grant predicates. This is a **Baseline assumption** selected for normal additive RBAC; Phase 07 must compile it server-side and test it.
- [x] Define an empty stored `row_filter` object as an explicit unrestricted predicate only for a valid effective grant. It never converts an absent or `can_read = false` grant into access.
- [x] Define column gates: an effective table read grant plus an explicit `column_permissions.can_read` grant is required to project a column; `can_filter` permits that column only in approved predicates; `can_aggregate` permits aggregation only when the column is also readable; all other use is denied.
- [x] Define an allow-listed masking policy of `redact`, `last4`, and `hash`; a sensitive cached column with no explicit mask type defaults to `redact`. Do not allow `none`, arbitrary formatting expressions, or an LLM-selected mask policy.
- [x] Define the stored row-filter input as the restricted JSON DSL specified in Phase 07. Validate structure, column ownership, source data type compatibility, allowed context placeholders, depth, and clause count at write time; reject raw SQL, function calls, subqueries, arbitrary identifier strings, and client-provided tenant values.
- [x] Define the following permission-management routes as **Baseline assumptions, not Section 8 requirements**: `GET/POST /api/roles`, `PUT/DELETE /api/roles/{role_id}`, `PUT /api/users/{user_id}/roles`, `GET/POST /api/permissions/table`, `GET/PUT/DELETE /api/permissions/table/{permission_id}`, and `PUT /api/permissions/table/{permission_id}/columns`.
- [x] Make the baseline role-create/update payload contain only `name` and `description`, and make `PUT /api/users/{user_id}/roles` atomically replace the tenant-local `role_ids` set after validating every role belongs to the active tenant.
- [x] Make the baseline table-permission payload require one `role_id` or `user_id`, `connection_id`, `table_id`, explicit operation flags, and a validated `row_filter`; prohibit callers from providing `tenant_id`, schema names, raw SQL, or encryption/connection values.
- [x] Make `PUT /api/permissions/table/{permission_id}/columns` atomically replace the grant's column rules with entries containing `column_id`, `can_read`, `can_filter`, `can_aggregate`, and optional allow-listed `mask_type`; verify every column belongs to the permission's table.
- [x] Require tenant-admin authorization for every baseline role and permission-management route. A tenant administrator may manage grants but still does not receive automatic access to live source-table data.
- [x] Validate same-tenant ownership across permission subjects and targets in one transaction: user/role, connection, table, schema, column, and permission must all resolve through the active tenant; reject cross-connection table/column combinations.
- [x] Preserve destructive foreign-key behavior from Section 7 and warn/audit on role, user, connection, table, or column removal because required cascades can remove dependent memberships or permission rows.
- [x] Emit safe audit events for role membership and permission changes with actor, tenant, action, target identifiers, and non-secret policy summary; do not store passwords, credentials, raw source rows, or unrestricted samples.
- [x] Publish a policy-service contract for Phase 07 that returns effective permissions and validated filter definitions, not mutable ORM entities or LLM-editable SQL fragments.

## Data Model Touched

- [x] Preserve `roles`: UUID primary key defaulting to `uuid_generate_v4()`, tenant foreign key with `ON DELETE CASCADE`, non-null `name`, nullable `description`, non-null `created_at` default, and `uq_roles_tenant_name`.
- [x] Preserve `user_roles`: `user_id` and `role_id` foreign keys with `ON DELETE CASCADE`, creation timestamp default, and composite primary key `(user_id, role_id)`.
- [x] Preserve `table_permissions`: UUID primary key default; tenant, connection, and table foreign keys with `ON DELETE CASCADE`; nullable role/user foreign keys with `ON DELETE CASCADE`; `can_read` default `TRUE`; insert/update/delete defaults `FALSE`; non-null `row_filter JSONB` default `{}`; creation timestamp; and `chk_permission_subject`.
- [x] Preserve `column_permissions`: UUID primary key default; `table_permission_id` and `column_id` foreign keys with `ON DELETE CASCADE`; read/filter/aggregate defaults `TRUE`; nullable `mask_type`; and `uq_column_permission`.
- [x] Add only the documented partial-unique-index baseline extension for unambiguous permission subjects; do not alter the required columns, defaults, foreign-key actions, checks, or unique constraints.
- [x] Read tenant-scoped `database_connections`, `database_tables`, and `database_columns` to validate grant targets; Phase 06 remains the owner of discovered metadata mutation.

## API Endpoints Touched

- [x] No permission-management path is required by Section 8; implement the explicit **Baseline assumption** routes listed in Detailed Tasks only after documenting them in the API manifest.
- [x] Keep required Section 8 connection and metadata routes unchanged; permission management augments their administration workflow and must not rename, replace, or imply additional Section 8 obligations.
- [x] Ensure every baseline management response is tenant-scoped and omits hidden schemas, connection credentials, raw samples, and other tenants' role or grant data.

## Security & Permission Notes

- [x] Enforce deny-by-default at table, column, operation, connection, tenant, and resource-ownership boundaries; authorization must happen before schema disclosure, LLM prompting, source SQL generation, or source execution.
- [x] Never let a role name, direct grant, row filter, column ID, mask type, or management request cross a tenant boundary, even if a caller knows a valid UUID.
- [x] Treat stored row filters as backend policy input, not user or LLM SQL; only the constrained compiler in Phase 07 may turn them into parameterized AST predicates.
- [x] Do not allow the generic chat path to use `can_insert`, `can_update`, or `can_delete`; normal chat stays read-only even if a future approved workflow stores such grants.
- [x] Ensure sensitive values are masked before prompts, results, logs, previews, citations, or final answers. Metadata and policy routes expose only the minimum information needed for administration.

## Testing Requirements

- [x] Unit-test role uniqueness, exclusive permission subjects, partial-unique extension behavior, tenant-local membership replacement, and same-tenant target validation.
- [x] Test direct-user allow and deny precedence over role grants, additive role access, no-grant denial, disabled-table denial, and inactive-connection denial.
- [x] Test column projection/filter/aggregate gates and all allowed mask types, including the sensitive-column default to `redact`.
- [x] Test malformed row-filter DSL input, unknown keys, raw SQL, source-table/column mismatch, invalid context placeholder, excessive depth, and incompatible value types are rejected before persistence.
- [x] Integration-test that only tenant administrators can use the baseline management endpoints and that cross-tenant role, user, table, column, and permission IDs yield safe non-enumerating failures.
- [x] Test that audit records for grant changes contain safe identifiers and policy summaries but no connection credentials, source results, or unmasked sensitive values.

## Definition of Done

- [x] Roles, memberships, direct grants, role grants, column grants, and masks have one documented fail-closed interpretation (see [docs/ACCEPTANCE_CRITERIA_PERMISSIONS.md](file:///d:/PROJECTS/ITI%20Project/docs/ACCEPTANCE_CRITERIA_PERMISSIONS.md)).
- [x] Non-PDF permission-management routes are clearly labeled baseline assumptions and do not change the required Section 8 contract.
- [x] Every saved permission target is tenant-consistent and every row filter is constrained policy data rather than executable SQL.
- [x] Later phases can resolve deterministic effective permissions without relying on tenant-admin bypass or LLM decisions.

## Suggested Day (1–4)

Day 2
