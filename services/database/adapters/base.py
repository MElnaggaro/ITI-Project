"""Capability-oriented adapter contract for controlled source databases."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class UnsupportedAdapterOperationError(RuntimeError):
    """Raised when a dialect has not implemented a controlled capability."""


@dataclass(frozen=True, slots=True)
class DialectCapabilities:
    """Capabilities must be explicit before a dialect is advertised as supported."""

    dialect: str
    supports_connection_testing: bool = False
    supports_schema_discovery: bool = False
    supports_readonly_execution: bool = False
    supports_ast_validation: bool = False


class DatabaseAdapter(ABC):
    """Future adapters expose only controlled, permission-aware operations."""

    capabilities: DialectCapabilities

    @abstractmethod
    async def test_connection(self, connection: Any) -> None:
        """Test a connection without exposing credentials or source rows."""

    @abstractmethod
    async def discover_schema(self, connection: Any) -> Any:
        """Return approved metadata only; never copy business records."""

    @abstractmethod
    async def execute_readonly(self, connection: Any, query: Any) -> Any:
        """Execute only a previously validated, bounded read-only plan."""
