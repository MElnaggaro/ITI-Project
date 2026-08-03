"""Unit tests for SQLGeneratorService candidate generation and prompt context formatting."""

from uuid import uuid4

import pytest

from core.tenant_context import TenantContext
from schemas.resolved_schema import ResolvedColumn, ResolvedSchema, ResolvedTable
from services.sql_generator_service import SQLGeneratorService


def test_sql_generator_prompt_formatting():
    """Verify prompt context contains only permitted tables and columns."""
    tenant_id = uuid4()
    user_id = uuid4()
    conn_id = uuid4()
    context = TenantContext(tenant_id=tenant_id, user_id=user_id)

    col1 = ResolvedColumn(column_id=uuid4(), column_name="id", data_type="uuid", is_primary_key=True, is_foreign_key=False, can_read=True, can_filter=True, can_aggregate=True)
    col2 = ResolvedColumn(column_id=uuid4(), column_name="email", data_type="varchar", is_primary_key=False, is_foreign_key=False, can_read=True, can_filter=True, can_aggregate=False)

    tbl = ResolvedTable(
        table_id=uuid4(),
        schema_name="public",
        table_name="users",
        table_type="table",
        description="Users table",
        can_read=True,
        can_insert=False,
        can_update=False,
        can_delete=False,
        columns={"id": col1, "email": col2},
    )

    resolved_schema = ResolvedSchema(
        tenant_id=tenant_id,
        user_id=user_id,
        connection_id=conn_id,
        database_type="postgresql",
        tables={"users": tbl},
    )

    generator = SQLGeneratorService()
    prompt_context = generator.format_schema_prompt_context(resolved_schema)

    assert "public.users" in prompt_context
    assert "id: uuid (PK)" in prompt_context
    assert "email: varchar" in prompt_context

    candidate = generator.generate_candidate(context, "Show all users", resolved_schema)
    assert candidate.candidate_sql is not None
    assert "public.users" in candidate.candidate_sql


def test_sql_generator_empty_schema_rejection():
    """Verify generator rejects empty schema."""
    context = TenantContext(tenant_id=uuid4(), user_id=uuid4())
    resolved_schema = ResolvedSchema(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        connection_id=uuid4(),
        database_type="postgresql",
    )

    generator = SQLGeneratorService()
    with pytest.raises(ValueError, match="empty or unpermitted schema"):
        generator.format_schema_prompt_context(resolved_schema)

    with pytest.raises(ValueError, match="No readable tables permitted"):
        generator.generate_candidate(context, "Show all users", resolved_schema)
