"""Unit tests for RowFilterCompiler AST compilation and placeholder resolution."""

from uuid import uuid4

import sqlglot
import sqlglot.expressions as exp
import pytest

from core.tenant_context import TenantContext
from services.row_filter_compiler import RowFilterCompiler


def test_row_filter_compiler_operators_and_context():
    """Verify JSON DSL filter compilation to SQLGlot AST expressions."""
    tenant_id = uuid4()
    user_id = uuid4()
    context = TenantContext(tenant_id=tenant_id, user_id=user_id)
    compiler = RowFilterCompiler(context)

    # 1. Simple EQ operator with tenant context placeholder
    node1 = {"tenant_id": {"eq": {"context": "tenant.id"}}}
    ast1 = compiler.compile(node1)
    assert isinstance(ast1, exp.EQ)
    assert ast1.sql() == f"tenant_id = '{tenant_id}'"

    # 2. Comparison operators (GT, LTE)
    node2 = {"age": {"gte": 18}}
    ast2 = compiler.compile(node2)
    assert isinstance(ast2, exp.GTE)
    assert ast2.sql() == "age >= 18"

    # 3. AND logical operator group
    node3 = {
        "and": [
            {"status": {"eq": "active"}},
            {"user_id": {"eq": {"context": "user.id"}}},
        ]
    }
    ast3 = compiler.compile(node3)
    assert isinstance(ast3, exp.And)
    assert f"user_id = '{user_id}'" in ast3.sql()
    assert "status = 'active'" in ast3.sql()


def test_row_filter_compiler_invalid_placeholder():
    """Verify compiler raises ValueError for unknown context placeholders."""
    context = TenantContext(tenant_id=uuid4(), user_id=uuid4())
    compiler = RowFilterCompiler(context)

    node = {"field": {"eq": {"context": "unsupported.placeholder"}}}
    with pytest.raises(ValueError, match="Unknown context placeholder"):
        compiler.compile(node)
