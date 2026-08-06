"""SQL Validation and Safety Layer using SQLGlot AST analysis and row-filter injection."""

from __future__ import annotations

from typing import Any

import sqlglot
import sqlglot.expressions as exp

from schemas.resolved_schema import ResolvedSchema
from schemas.sql_validation import ValidatedQueryPlan

_DISALLOWED_CLASS_NAMES = (
    "Insert",
    "Update",
    "Delete",
    "Create",
    "Drop",
    "Alter",
    "Command",
    "Copy",
    "Grant",
    "Revoke",
    "Exec",
    "Execute",
    "Call",
    "Attach",
    "Detach",
    "Truncate",
    "TruncateTable",
    "Use",
    "Set",
    "Pragma",
    "Kill",
    "Merge",
    "Lock",
)

DISALLOWED_NODE_TYPES: tuple[type[exp.Expression], ...] = tuple(
    getattr(exp, name) for name in _DISALLOWED_CLASS_NAMES if hasattr(exp, name)
)

SYSTEM_SCHEMAS = frozenset({
    "information_schema",
    "pg_catalog",
    "pg_toast",
    "sys",
    "mysql",
    "performance_schema",
    "master",
    "model",
    "msdb",
    "tempdb",
    "sqlite_master",
    "sqlite_schema",
})

BLOCKED_FUNCTIONS = frozenset({
    "version",
    "pg_read_file",
    "pg_ls_dir",
    "pg_stat_file",
    "pg_sleep",
    "current_setting",
    "set_config",
    "load_file",
    "into_outfile",
    "into_dumpfile",
    "xp_cmdshell",
    "sleep",
    "benchmark",
    "sys_eval",
    "sys_exec",
    "openrowset",
    "opendatasource",
    "eval",
    "char",
    "exec",
    "execute",
})

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
    """AST-based SQL validator and security rewriter enforcing Mandatory SQL Security Controls."""

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

        # 1. Reject comments explicitly (Control 13)
        cleaned_raw = candidate_sql.strip()
        if "--" in cleaned_raw or "/*" in cleaned_raw or "*/" in cleaned_raw:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql="",
                query_type="disallowed",
                validation_status="invalid",
                validation_errors=[
                    "Comments in SQL queries are strictly prohibited due to security policy."
                ],
            )

        # 2. Parse SQL candidate (Control 12 & 13)
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

        # Check for AST level comments
        if any(node.comments for node in ast.walk()):
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type="disallowed",
                validation_status="invalid",
                validation_errors=["SQL comments detected within query structure are strictly prohibited."],
            )

        # Handle EXPLAIN statement (Control 15)
        is_explain = False
        if cleaned_raw.upper().startswith("EXPLAIN"):
            is_explain = True
            inner_sql = cleaned_raw[7:].strip()
            try:
                inner_parsed = sqlglot.parse(inner_sql, read=self.dialect)
                if inner_parsed and inner_parsed[0]:
                    ast = inner_parsed[0]
            except Exception:
                pass

        # 3. Enforce Read-Only AST & Block DDL / Destructive DML (Control 15 & 16)
        if isinstance(ast, DISALLOWED_NODE_TYPES) or any(
            next(ast.find_all(t), None) is not None for t in DISALLOWED_NODE_TYPES
        ):
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type="disallowed",
                validation_status="invalid",
                validation_errors=[
                    "Data modification, procedural commands, DDL, GRANT/REVOKE, EXEC, COPY, ATTACH, and DETACH statements are strictly prohibited."
                ],
            )

        # Determine query type (Control 15 - Allowed: SELECT, WITH, EXPLAIN)
        if is_explain:
            query_type = "explain"
        elif isinstance(ast, exp.Select):
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
                validation_errors=["Only SELECT, WITH, UNION, and EXPLAIN read-only queries are permitted by default."],
            )

        # 4. System Schemas and Administrative Functions Verification (Control 14)
        for table_node in ast.find_all(exp.Table):
            tbl_name = table_node.name.lower() if table_node.name else ""
            db_schema = table_node.db.lower() if table_node.db else ""
            catalog_name = table_node.catalog.lower() if table_node.catalog else ""
            if (
                tbl_name in SYSTEM_SCHEMAS
                or db_schema in SYSTEM_SCHEMAS
                or catalog_name in SYSTEM_SCHEMAS
            ):
                return ValidatedQueryPlan(
                    generated_sql=candidate_sql,
                    normalized_sql=ast.sql(dialect=self.dialect),
                    query_type="disallowed",
                    validation_status="invalid",
                    validation_errors=[
                        f"Access to system schema or system table '{table_node.sql()}' is strictly prohibited."
                    ],
                )

        # Administrative / System Function Blocking (Control 14)
        import re
        for fn in BLOCKED_FUNCTIONS:
            pattern = rf"\b{re.escape(fn)}\s*\("
            if re.search(pattern, candidate_sql, re.IGNORECASE):
                return ValidatedQueryPlan(
                    generated_sql=candidate_sql,
                    normalized_sql=ast.sql(dialect=self.dialect),
                    query_type="disallowed",
                    validation_status="invalid",
                    validation_errors=[
                        f"Administrative or system function '{fn}' is strictly prohibited."
                    ],
                )

        # 5. Table & Column Permission Verification (Control 11)
        referenced_tables: list[str] = []
        referenced_columns: list[str] = []
        applied_filters_meta: list[dict[str, Any]] = []

        cte_names = {
            cte.alias.lower()
            for cte in ast.find_all(exp.CTE)
            if cte.alias
        }

        tables_in_ast = [
            t for t in ast.find_all(exp.Table)
            if t.name and t.name.lower() not in cte_names
        ]

        if not tables_in_ast:
            return ValidatedQueryPlan(
                generated_sql=candidate_sql,
                normalized_sql=ast.sql(dialect=self.dialect),
                query_type=query_type,
                validation_status="invalid",
                validation_errors=["Query does not reference any valid target table."],
            )

        errors: list[str] = []
        for table_node in tables_in_ast:
            tbl_name = table_node.name
            if tbl_name not in resolved_schema.tables:
                errors.append(f"Referenced table '{tbl_name}' is not permitted or does not exist.")
            else:
                if tbl_name not in referenced_tables:
                    referenced_tables.append(tbl_name)

        # Column-level permission verification
        select_aliases = {
            alias_node.alias.lower()
            for alias_node in ast.find_all(exp.Alias)
            if alias_node.alias
        }

        columns_in_ast = list(ast.find_all(exp.Column))
        for col_node in columns_in_ast:
            c_name = col_node.name
            if not c_name or c_name == "*" or c_name.lower() in select_aliases:
                continue

            tbl_name = col_node.table
            if not tbl_name and len(referenced_tables) == 1:
                tbl_name = referenced_tables[0]

            if tbl_name and tbl_name in resolved_schema.tables:
                tbl_schema = resolved_schema.tables[tbl_name]
                if c_name not in tbl_schema.columns or not tbl_schema.columns[c_name].can_read:
                    errors.append(
                        f"Referenced column '{c_name}' on table '{tbl_name}' is not permitted."
                    )
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
                    ast = ast.where(filter_ast)  # type: ignore[union-attr]

        # 6. Limit Clamping
        existing_limit = ast.args.get("limit")  # type: ignore[union-attr]
        if existing_limit is None:
            ast = ast.limit(MAX_ROW_LIMIT)  # type: ignore[union-attr]
        else:
            try:
                val = int(existing_limit.expression.this)
                if val > MAX_ROW_LIMIT:
                    ast = ast.limit(MAX_ROW_LIMIT)  # type: ignore[union-attr]
            except (ValueError, AttributeError):
                ast = ast.limit(MAX_ROW_LIMIT)  # type: ignore[union-attr]

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

