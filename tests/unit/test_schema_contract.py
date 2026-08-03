"""Schema contract unit tests verifying all 18 Section 7 PostgreSQL tables."""

from __future__ import annotations

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from models import (
    AuditLog,
    Base,
    ColumnPermission,
    Conversation,
    DatabaseColumn,
    DatabaseConnection,
    DatabaseSchema,
    DatabaseTable,
    DocumentChunk,
    File,
    KnowledgeBase,
    Message,
    MessageCitation,
    QueryExecution,
    Role,
    TablePermission,
    Tenant,
    User,
    UserRole,
)


def test_schema_contract_all_18_tables_present():
    """Assert all 18 Section 7 core tables are defined in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "tenants",
        "users",
        "roles",
        "user_roles",
        "database_connections",
        "database_schemas",
        "database_tables",
        "database_columns",
        "table_permissions",
        "column_permissions",
        "knowledge_bases",
        "files",
        "document_chunks",
        "conversations",
        "messages",
        "query_executions",
        "message_citations",
        "audit_logs",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


def test_explicit_indexes():
    """Assert required explicit non-unique indexes exist on users and database_connections."""
    users_table = Base.metadata.tables["users"]
    db_conn_table = Base.metadata.tables["database_connections"]

    user_idx_names = {idx.name for idx in users_table.indexes}
    assert "idx_users_tenant_id" in user_idx_names

    db_conn_idx_names = {idx.name for idx in db_conn_table.indexes}
    assert "idx_database_connections_tenant" in db_conn_idx_names


def test_unique_constraints_fidelity():
    """Assert required unique constraints exist across Section 7 schema."""
    tenants_t = Base.metadata.tables["tenants"]
    users_t = Base.metadata.tables["users"]
    roles_t = Base.metadata.tables["roles"]
    db_conn_t = Base.metadata.tables["database_connections"]
    db_schema_t = Base.metadata.tables["database_schemas"]
    db_table_t = Base.metadata.tables["database_tables"]
    db_col_t = Base.metadata.tables["database_columns"]
    col_perm_t = Base.metadata.tables["column_permissions"]
    kb_t = Base.metadata.tables["knowledge_bases"]
    doc_chunk_t = Base.metadata.tables["document_chunks"]

    # Tenants code uniqueness
    code_col = tenants_t.columns["code"]
    assert code_col.unique or any(
        isinstance(c, UniqueConstraint) and "code" in [col.name for col in c.columns]
        for c in tenants_t.constraints
    )

    # Users uq_users_tenant_email
    u_uqs = {c.name for c in users_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_users_tenant_email" in u_uqs

    # Roles uq_roles_tenant_name
    r_uqs = {c.name for c in roles_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_roles_tenant_name" in r_uqs

    # Database connections uq_database_connection_name
    dbc_uqs = {c.name for c in db_conn_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_database_connection_name" in dbc_uqs

    # Database schemas uq_database_schema
    dbs_uqs = {c.name for c in db_schema_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_database_schema" in dbs_uqs

    # Database tables uq_database_table
    dbt_uqs = {c.name for c in db_table_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_database_table" in dbt_uqs

    # Database columns uq_database_column
    dbc_cols_uqs = {c.name for c in db_col_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_database_column" in dbc_cols_uqs

    # Column permissions uq_column_permission
    cp_uqs = {c.name for c in col_perm_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_column_permission" in cp_uqs

    # Knowledge bases uq_knowledge_base_name
    kb_uqs = {c.name for c in kb_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_knowledge_base_name" in kb_uqs

    # Document chunks uq_document_chunk
    dc_uqs = {c.name for c in doc_chunk_t.constraints if isinstance(c, UniqueConstraint)}
    assert "uq_document_chunk" in dc_uqs


def test_table_permissions_check_constraint():
    """Assert table_permissions has chk_permission_subject check constraint."""
    table_perm_t = Base.metadata.tables["table_permissions"]
    check_constraints = [c for c in table_perm_t.constraints if isinstance(c, CheckConstraint)]
    assert any("chk_permission_subject" in (c.name or "") for c in check_constraints)


def test_foreign_key_ondelete_actions():
    """Assert ON DELETE actions (CASCADE and SET NULL) on Section 7 foreign keys."""
    users_t = Base.metadata.tables["users"]
    fk_users_tenant = [c for c in users_t.constraints if isinstance(c, ForeignKeyConstraint)][0]
    assert fk_users_tenant.ondelete == "CASCADE"

    db_conn_t = Base.metadata.tables["database_connections"]
    fk_map = {
        c.columns[0].name: c.ondelete
        for c in db_conn_t.constraints
        if isinstance(c, ForeignKeyConstraint)
    }
    assert fk_map["tenant_id"] == "CASCADE"
    assert fk_map["created_by"] == "SET NULL"


def test_user_roles_composite_primary_key():
    """Assert user_roles table has a composite primary key (user_id, role_id)."""
    user_roles_t = Base.metadata.tables["user_roles"]
    pk_cols = [c.name for c in user_roles_t.primary_key.columns]
    assert set(pk_cols) == {"user_id", "role_id"}
