"""Row filter AST compiler using SQLGlot to convert JSON DSL predicates into safe SQL AST expressions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import sqlglot
import sqlglot.expressions as exp

from core.tenant_context import TenantContext


class RowFilterCompiler:
    """Compiles row-filter JSON DSL conditions into SQLGlot AST Expressions."""

    def __init__(self, context: TenantContext) -> None:
        self.context = context

    def resolve_value(self, val: Any) -> exp.Expression:
        """Resolve literal or context placeholder to SQLGlot literal AST."""
        if isinstance(val, dict) and "context" in val:
            ctx_key = str(val["context"]).lower()
            if ctx_key == "tenant.id":
                return exp.Literal.string(str(self.context.tenant_id))
            elif ctx_key == "user.id":
                return exp.Literal.string(str(self.context.user_id))
            else:
                raise ValueError(f"Unknown context placeholder: '{val['context']}'")
        elif isinstance(val, bool):
            return exp.Boolean(this=val)
        elif isinstance(val, (int, float)):
            return exp.Literal.number(val)
        elif isinstance(val, str):
            return exp.Literal.string(val)
        elif isinstance(val, list):
            return exp.Tuple(expressions=[self.resolve_value(item) for item in val])
        elif val is None:
            return exp.null()
        else:
            raise ValueError(f"Unsupported filter literal type: {type(val)}")

    def compile(self, node: dict[str, Any]) -> exp.Expression | None:
        """Recursively compile a JSON DSL node into a SQLGlot Expression."""
        if not node:
            return None

        for key, val in node.items():
            key_lower = str(key).lower()
            if key_lower == "and":
                if not isinstance(val, list) or not val:
                    raise ValueError("'and' filter group requires a non-empty list.")
                compiled_items = [self.compile(item) for item in val]
                valid_items = [c for c in compiled_items if c is not None]
                if not valid_items:
                    return None
                result = valid_items[0]
                for item in valid_items[1:]:
                    result = exp.And(this=result, expression=item)
                return result

            elif key_lower == "or":
                if not isinstance(val, list) or not val:
                    raise ValueError("'or' filter group requires a non-empty list.")
                compiled_items = [self.compile(item) for item in val]
                valid_items = [c for c in compiled_items if c is not None]
                if not valid_items:
                    return None
                result = valid_items[0]
                for item in valid_items[1:]:
                    result = exp.Or(this=result, expression=item)
                return result

            else:
                # Direct column clause check e.g. {"status": {"eq": "active"}} or {"eq": {"column": "status", "value": "active"}}
                if isinstance(val, dict):
                    col_name = key
                    for op_name, raw_val in val.items():
                        return self._compile_op(col_name, str(op_name).lower(), raw_val)

        raise ValueError(f"Unable to compile row_filter node: {node}")

    def _compile_op(self, col_name: str, op_name: str, raw_val: Any) -> exp.Expression:
        column_expr = exp.Column(this=exp.Identifier(this=col_name, quoted=False))
        val_expr = self.resolve_value(raw_val)

        if op_name == "eq":
            return exp.EQ(this=column_expr, expression=val_expr)
        elif op_name == "ne":
            return exp.NEQ(this=column_expr, expression=val_expr)
        elif op_name == "gt":
            return exp.GT(this=column_expr, expression=val_expr)
        elif op_name == "gte":
            return exp.GTE(this=column_expr, expression=val_expr)
        elif op_name == "lt":
            return exp.LT(this=column_expr, expression=val_expr)
        elif op_name == "lte":
            return exp.LTE(this=column_expr, expression=val_expr)
        elif op_name == "in":
            return exp.In(this=column_expr, query=val_expr)
        elif op_name == "like":
            return exp.Like(this=column_expr, expression=val_expr)
        elif op_name == "is_null":
            return exp.Is(this=column_expr, expression=exp.null())
        else:
            raise ValueError(f"Unsupported row_filter compiler operator: '{op_name}'")
