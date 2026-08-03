"""Database source adapter layer providing safe read-only connectivity probes and SSRF host filtering."""

from __future__ import annotations

from abc import ABC, abstractmethod
import ipaddress
import socket
from typing import Any

from sqlalchemy import create_engine, text

DISALLOWED_HOSTNAMES = frozenset({"localhost", "loopback", "metadata.google.internal"})


def validate_host_ssrf(host: str | None) -> None:
    """Validate target host to prevent SSRF and internal network probing."""
    if not host:
        return
    cleaned_host = host.strip().lower()

    if cleaned_host in DISALLOWED_HOSTNAMES:
        raise ValueError(f"Connection host '{host}' is disallowed due to SSRF security policy.")

    ip_obj = None
    try:
        ip_obj = ipaddress.ip_address(cleaned_host)
    except ValueError:
        pass

    if ip_obj is not None:
        if ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
            raise ValueError(f"Connection host IP '{host}' is disallowed due to network isolation policy.")
    else:
        try:
            resolved_ip_str = socket.gethostbyname(cleaned_host)
            resolved_ip = ipaddress.ip_address(resolved_ip_str)
            if resolved_ip.is_loopback or resolved_ip.is_link_local or resolved_ip.is_multicast:
                raise ValueError(f"Target host '{host}' resolves to restricted IP '{resolved_ip_str}'.")
        except socket.gaierror:
            pass


class BaseSourceAdapter(ABC):
    """Abstract source adapter contract for database integration."""

    @abstractmethod
    def test_connection(self, timeout_seconds: int = 5) -> tuple[bool, str]:
        """Perform a safe read-only connectivity health probe."""
        ...

    @abstractmethod
    def build_connection_string(self) -> str:
        """Construct driver-specific connection string."""
        ...


class PostgreSQLAdapter(BaseSourceAdapter):
    """Supported baseline adapter for live PostgreSQL source databases."""

    def __init__(
        self,
        host: str | None,
        port: int | None,
        database_name: str | None,
        username: str | None,
        password: str | None,
        connection_string: str | None = None,
        ssl_enabled: bool = False,
        ssl_settings: dict[str, Any] | None = None,
        connection_options: dict[str, Any] | None = None,
    ) -> None:
        self.host = host
        self.port = port or 5432
        self.database_name = database_name
        self.username = username
        self.password = password
        self.raw_connection_string = connection_string
        self.ssl_enabled = ssl_enabled
        self.ssl_settings = ssl_settings or {}
        self.connection_options = connection_options or {}

        # Validate SSRF
        validate_host_ssrf(self.host)

    def build_connection_string(self) -> str:
        if self.raw_connection_string:
            return self.raw_connection_string
        ssl_mode = "require" if self.ssl_enabled else "disable"
        return f"postgresql+psycopg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?sslmode={ssl_mode}"

    def test_connection(self, timeout_seconds: int = 5) -> tuple[bool, str]:
        """Perform minimal read-only probe `SELECT 1`."""
        conn_str = self.build_connection_string()
        try:
            engine = create_engine(
                conn_str,
                connect_args={"connect_timeout": timeout_seconds},
                pool_pre_ping=True,
            )
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                if result == 1:
                    return True, "PostgreSQL connection test successful."
                return False, "Unexpected health probe response."
        except Exception as e:
            # Redact error details to prevent credential/internal leakage
            err_msg = str(e).split("\n")[0]
            return False, f"PostgreSQL connection test failed: {err_msg[:150]}"


class ExtensionSourceAdapter(BaseSourceAdapter):
    """Stub adapter for unsupported future dialects (MySQL, SQL Server, Oracle)."""

    def __init__(self, dialect: str) -> None:
        self.dialect = dialect

    def build_connection_string(self) -> str:
        raise NotImplementedError(f"{self.dialect} dialect is an extension point not yet supported.")

    def test_connection(self, timeout_seconds: int = 5) -> tuple[bool, str]:
        return False, f"Dialect '{self.dialect}' is an unsupported extension adapter in this baseline."


def get_source_adapter(
    database_type: str,
    host: str | None,
    port: int | None,
    database_name: str | None,
    username: str | None,
    password: str | None,
    connection_string: str | None = None,
    ssl_enabled: bool = False,
    ssl_settings: dict[str, Any] | None = None,
    connection_options: dict[str, Any] | None = None,
) -> BaseSourceAdapter:
    """Return configured source adapter instance."""
    normalized_type = database_type.strip().lower()
    if normalized_type == "postgresql":
        return PostgreSQLAdapter(
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password,
            connection_string=connection_string,
            ssl_enabled=ssl_enabled,
            ssl_settings=ssl_settings,
            connection_options=connection_options,
        )
    return ExtensionSourceAdapter(dialect=database_type)
