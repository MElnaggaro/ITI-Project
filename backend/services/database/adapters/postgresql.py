"""PostgreSQL adapter boundary; controlled implementation is owned by Phase 05."""

from __future__ import annotations

from typing import Any

from services.database.adapters.base import (
    DatabaseAdapter,
    DialectCapabilities,
    UnsupportedAdapterOperationError,
)


class PostgreSQLAdapter(DatabaseAdapter):
    """Planned end-to-end source adapter; not advertised as ready in Phase 01."""

    capabilities = DialectCapabilities(dialect="postgresql")

    async def test_connection(self, connection: Any) -> None:
        raise UnsupportedAdapterOperationError("PostgreSQL connection testing begins in Phase 05")

    async def discover_schema(self, connection: Any) -> Any:
        raise UnsupportedAdapterOperationError("PostgreSQL schema discovery begins in Phase 06")

    async def execute_readonly(self, connection: Any, query: Any) -> Any:
        raise UnsupportedAdapterOperationError("PostgreSQL execution begins in Phase 10")
