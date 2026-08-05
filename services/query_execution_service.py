"""Query Execution Service running validated plans under bounded resources and masking rules."""

from __future__ import annotations

import hashlib
import time
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from core.encryption import decrypt_secret
from core.tenant_context import TenantContext
from models.database_connection import DatabaseConnection
from models.query_execution import QueryExecution
from repositories.connection_repository import ConnectionRepository
from repositories.query_execution_repository import QueryExecutionRepository
from schemas.query_execution import ExecutionResultEnvelope
from schemas.resolved_schema import ResolvedSchema
from schemas.sql_validation import ValidatedQueryPlan


def apply_masking(val: Any, mask_type: str | None) -> Any:
    """Apply masking policy (redact, last4, hash) on a sensitive column value."""
    if val is None or not mask_type:
        return val

    str_val = str(val)
    if mask_type == "redact":
        return "[REDACTED]"
    elif mask_type == "last4":
        if len(str_val) <= 4:
            return "****"
        return "*" * (len(str_val) - 4) + str_val[-4:]
    elif mask_type == "hash":
        return hashlib.sha256(str_val.encode("utf-8")).hexdigest()[:16]
    return "[REDACTED]"


class QueryExecutionService:
    """Executes ValidatedQueryPlan instances against source database."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.conn_repo = ConnectionRepository(session)
        self.exec_repo = QueryExecutionRepository(session)

    def execute_plan(
        self,
        context: TenantContext,
        connection_id: UUID,
        validated_plan: ValidatedQueryPlan,
        resolved_schema: ResolvedSchema | None = None,
        conversation_id: UUID | None = None,
        message_id: UUID | None = None,
        timeout_seconds: int = 30,
    ) -> ExecutionResultEnvelope:
        """Execute validated query plan and record sanitized QueryExecution audit trail."""
        if validated_plan.validation_status != "valid" or not validated_plan.final_sql:
            raise ValueError("Cannot execute invalid query plan.")

        conn = self.conn_repo.get_by_id(context.tenant_id, connection_id)
        if not conn or not conn.is_active:
            raise ValueError("Database connection not found or inactive.")

        plain_pass = decrypt_secret(conn.encrypted_password, context.tenant_id)
        plain_conn_str = decrypt_secret(conn.encrypted_connection_string, context.tenant_id)

        from services.database.adapter import get_source_adapter
        adapter = get_source_adapter(
            database_type=conn.database_type,
            host=conn.host,
            port=conn.port,
            database_name=conn.database_name,
            username=conn.username,
            password=plain_pass,
            connection_string=plain_conn_str,
            ssl_enabled=conn.ssl_enabled,
            ssl_settings=conn.ssl_settings,
            connection_options=conn.connection_options,
        )
        conn_str = adapter.build_connection_string()

        start_time = time.perf_counter()
        rows: list[dict[str, Any]] = []
        columns: list[str] = []
        exec_status = "success"
        error_msg = None

        # Build column mask map from resolved_schema
        col_mask_map: dict[str, str] = {}
        if resolved_schema:
            for tbl in resolved_schema.tables.values():
                for c_name, c_obj in tbl.columns.items():
                    if c_obj.mask_type:
                        col_mask_map[c_name] = c_obj.mask_type

        try:
            engine = create_engine(
                conn_str,
                connect_args={"connect_timeout": timeout_seconds},
                pool_pre_ping=True,
            )
            with engine.connect() as source_conn:
                cursor_result = source_conn.execute(text(validated_plan.final_sql))
                columns = list(cursor_result.keys())

                for raw_row in cursor_result.mappings():
                    row_dict = {}
                    for col_name, val in raw_row.items():
                        mask_type = col_mask_map.get(col_name)
                        row_dict[col_name] = apply_masking(val, mask_type)
                    rows.append(row_dict)

            engine.dispose()
        except Exception as e:
            exec_status = "failed"
            error_msg = str(e).split("\n")[0][:200]

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        from datetime import datetime as PyDatetime
        def _json_safe(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_json_safe(i) for i in obj]
            elif isinstance(obj, (UUID, PyDatetime)):
                return str(obj)
            return obj

        # Sanitized result preview (first 5 rows max)
        preview_rows = [_json_safe(r) for r in rows[:5]] if rows else []
        preview_data = {"columns": columns, "sample_rows": preview_rows} if preview_rows else None

        # Record QueryExecution
        q_exec = QueryExecution(
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
            message_id=message_id,
            connection_id=conn.id,
            generated_sql=validated_plan.generated_sql,
            normalized_sql=validated_plan.normalized_sql,
            query_type=validated_plan.query_type,
            validation_status=validated_plan.validation_status,
            validation_errors=validated_plan.validation_errors,
            applied_row_filters={"count": len(validated_plan.applied_row_filters)},
            referenced_tables=validated_plan.referenced_tables,
            referenced_columns=validated_plan.referenced_columns,
            execution_status=exec_status,
            execution_time_ms=latency_ms,
            returned_row_count=len(rows),
            result_preview=preview_data,
            error_message=error_msg,
        )

        self.exec_repo.create(q_exec)

        if exec_status == "failed":
            raise RuntimeError(f"Source query execution failed: {error_msg}")

        return ExecutionResultEnvelope(
            execution_id=q_exec.id,
            columns=columns,
            rows=rows,
            returned_row_count=len(rows),
            execution_time_ms=latency_ms,
            is_truncated=False,
        )
