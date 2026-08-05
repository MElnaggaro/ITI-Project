"""SQL Validation and Safety Layer using SQLGlot AST analysis and row-filter injection."""

from __future__ import annotations

from typing import Any

import sqlglot
import sqlglot.expressions as exp

from schemas.resolved_schema import ResolvedSchema
from schemas.sql_validation import ValidatedQueryPlan

DISALLOWED_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Copy,
)

MAX_ROW_LIMIT = 1000

DIALECT_MAP = {
    "postgresql": "postgres",
    "postgres": "postgres",
    "mysql": "mysql",
    "sqlserver": "tsql",
    "mssql": "tsql",
    "oracle": "oracle",
}


class SQLValidatorService:
    """AST-based SQL validator and security rewriter."""

    def __init__(self, dialect: str = "postgres") -> None:
        raw_dialect = dialect.strip().lower()
        self.dialect = DIALECT_MAP.get(raw_dialect, "postgres")

    def validate_and_rewrite(
        self,
        candidate_sql: str,
        resolved_schema: ResolvedSchema,
    ) -> ValidatedQueryPlan:
        """Parse, authorize, inject row filters and LIMIT, and re-validate candidate SQL."""
        if not candidate_sql or not candidate_sql.strip():
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql="",
                query_type="unknown",
                validation_status="invalid",
                validation_errors=["Candidate SQL string is empty."],
            )

        # 1. Reject comments explicitly
        cleaned_raw = candidate_sql.strip()
        if "--" in cleaned_raw or "/*" in cleaned_raw or "*/" in cleaned_raw:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql="",
                query_type="disallowed",
                validation_status="invalid",
                validation_errors=["Comments in SQL queries are strictly prohibited due to security policy."],
            )

        # 2. Parse SQL candidate
        try:
            parsed_statements = sqlglot.parse(candidate_sql, read=self.dialect)
        except Exception as e:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql="",
                query_type="unknown",
                validation_status="invalid",
                validation_errors=[f"SQL parser error: {str(e)[:150]}"],
            )

        if len(parsed_statements) != 1 or parsed_statements[0] is None:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql="",
                query_type="unknown",
                validation_status="invalid",
                validation_errors=["Only single SQL statements are permitted."],
            )

        ast = parsed_statements[0]
        errors: list[str] = []

        # 3. Enforce Read-Only AST
        if isinstance(ast, DISALLOWED_NODE_TYPES) or any(
            ast.find_all(DISALLOWED_NODE_TYPES)
        ):
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type="disallowed",
                validation_status="invalid",
                validation_errors=["Data modification, procedural commands, and DDL statements are strictly prohibited."],
            )

        # Determine query type
        if isinstance(ast, exp.Select):
            query_type = "select"
        elif isinstance(ast, exp.With):
            query_type = "with"
        elif isinstance(ast, exp.Union):
            query_type = "union"
        else:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type="disallowed",
                validation_status="invalid",
                validation_errors=["Only SELECT, WITH, and UNION read-only queries are permitted."],
            )

        # 4. Table & Column Permission Verification
        referenced_tables: list[str] = []
        referenced_columns: list[str] = []
        applied_filters_meta: list[dict[str, Any]] = []

        tables_in_ast = list(ast.find_all(exp.Table))
        if not tables_in_ast:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type=query_type,
                validation_status="invalid",
                validation_errors=["Query does not reference any valid target table."],
            )

        for table_node in tables_in_ast:
            tbl_name = table_node.name
            if tbl_name not in resolved_schema.tables:
                errors.append(f"Referenced table '{tbl_name}' is not permitted or does not exist.")
            else:
                if tbl_name not in referenced_tables:
                    referenced_tables.append(tbl_name)

        # Column-level permission verification
        columns_in_ast = list(ast.find_all(exp.Column))
        for col_node in columns_in_ast:
            c_name = col_node.name
            if not c_name or c_name == "*":
                continue

            tbl_name = col_node.table
            if not tbl_name and len(referenced_tables) == 1:
                tbl_name = referenced_tables[0]

            if tbl_name and tbl_name in resolved_schema.tables:
                tbl_schema = resolved_schema.tables[tbl_name]
                if c_name not in tbl_schema.columns or not tbl_schema.columns[c_name].can_read:
                    errors.append(f"Referenced column '{c_name}' on table '{tbl_name}' is not permitted.")
                else:
                    ref_col_str = f"{tbl_name}.{c_name}"
                    if ref_col_str not in referenced_columns:
                        referenced_columns.append(ref_col_str)

        if errors:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type=query_type,
                validation_status="invalid",
                validation_errors=errors,
            )

        # 5. Inject Row-Filter AST Expressions
        for tbl_name in referenced_tables:
            tbl = resolved_schema.tables[tbl_name]
            if tbl.compiled_row_filters:
                applied_filters_meta.extend(tbl.raw_row_filters)
                for filter_ast in tbl.compiled_row_filters:
                    ast = ast.where(filter_ast)

        # 6. Limit Clamping
        existing_limit = ast.args.get("limit")
        if existing_limit is None:
            ast = ast.limit(MAX_ROW_LIMIT)
        else:
            try:
                val = int(existing_limit.expression.this)
                if val > MAX_ROW_LIMIT:
                    ast = ast.limit(MAX_ROW_LIMIT)
            except (ValueError, AttributeError):
                ast = ast.limit(MAX_ROW_LIMIT)

        # 7. Final Re-Validation
        final_sql = ast.sql(dialect=self.dialect)

        return ValidatedQueryPlan(
            generated_sql=candidate_sql,
            normalized_sql=final_sql,
            query_type=query_type,
            validation_status="valid",
            validation_errors=[],
            referenced_tables=referenced_tables,
            referenced_columns=referenced_columns,
            applied_row_filters=applied_filters_meta,
            final_sql=final_sql,
        )

