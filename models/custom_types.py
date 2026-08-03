"""Custom SQLAlchemy column types for PostgreSQL extensions."""

from __future__ import annotations

from typing import Any

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    """pgvector VECTOR type mapping for SQLAlchemy DDL and query execution."""

    cache_ok = True

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def get_col_spec(self, **kw: Any) -> str:
        return f"VECTOR({self.dim})"

    def bind_processor(self, dialect: Dialect):
        def process(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, list):
                return str(value)
            return value

        return process

    def result_processor(self, dialect: Dialect, coltype: Any):
        def process(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, str):
                cleaned = value.strip("[]")
                if not cleaned:
                    return []
                return [float(x) for x in cleaned.split(",")]
            return value

        return process
