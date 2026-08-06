"""SQL Server extension-path adapter; unsupported until implemented and tested."""

from typing import Any

from services.database.adapters.base import (
    DatabaseAdapter,
    DialectCapabilities,
    UnsupportedAdapterOperationError,
)


class SQLServerAdapter(DatabaseAdapter):
    """Retain the module path without inheriting PostgreSQL capabilities."""

    capabilities = DialectCapabilities(dialect="sqlserver")

    async def test_connection(self, connection: Any) -> None:
        raise UnsupportedAdapterOperationError("SQL Server is not supported yet")

    async def discover_schema(self, connection: Any) -> Any:
        raise UnsupportedAdapterOperationError("SQL Server is not supported yet")

    async def execute_readonly(self, connection: Any, query: Any) -> Any:
        raise UnsupportedAdapterOperationError("SQL Server is not supported yet")
