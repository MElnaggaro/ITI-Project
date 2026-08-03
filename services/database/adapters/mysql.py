"""MySQL extension-path adapter; unsupported until implemented and tested."""

from typing import Any

from services.database.adapters.base import (
    DatabaseAdapter,
    DialectCapabilities,
    UnsupportedAdapterOperationError,
)


class MySQLAdapter(DatabaseAdapter):
    """Retain the module path without claiming implementation support."""

    capabilities = DialectCapabilities(dialect="mysql")

    async def test_connection(self, connection: Any) -> None:
        raise UnsupportedAdapterOperationError("MySQL is not supported yet")

    async def discover_schema(self, connection: Any) -> Any:
        raise UnsupportedAdapterOperationError("MySQL is not supported yet")

    async def execute_readonly(self, connection: Any, query: Any) -> Any:
        raise UnsupportedAdapterOperationError("MySQL is not supported yet")
