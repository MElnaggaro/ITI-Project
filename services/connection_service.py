"""Database Connection Service handling lifecycle, secret encryption, and connectivity tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from core.encryption import decrypt_secret, encrypt_secret
from core.tenant_context import TenantContext
from models.database_connection import DatabaseConnection
from repositories.connection_repository import ConnectionRepository
from schemas.database_connections import (
    ConnectionTestResponse,
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseConnectionUpdate,
)
from services.database.adapter import validate_host_ssrf, get_source_adapter


class ConnectionService:
    """Service orchestrating tenant database connections."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ConnectionRepository(session)

    def list_connections(self, tenant_id: UUID) -> list[DatabaseConnectionResponse]:
        """List all database connections for tenant."""
        conns = self.repo.list_by_tenant(tenant_id)
        return [DatabaseConnectionResponse.model_validate(c) for c in conns]

    def get_connection(self, tenant_id: UUID, connection_id: UUID) -> DatabaseConnectionResponse | None:
        """Get detail for a specific database connection with redacted secrets."""
        conn = self.repo.get_by_id(tenant_id, connection_id)
        if not conn:
            return None
        return DatabaseConnectionResponse.model_validate(conn)

    def create_connection(
        self,
        context: TenantContext,
        data: DatabaseConnectionCreate,
    ) -> DatabaseConnectionResponse:
        """Create a new database connection with encrypted credentials."""
        # 1. SSRF validation
        validate_host_ssrf(data.host)

        # 2. Check for duplicate name
        existing = self.repo.get_by_name(context.tenant_id, data.name)
        if existing:
            raise ValueError(f"Connection with name '{data.name}' already exists in this tenant.")

        # 3. Encrypt secrets bound to tenant_id
        enc_pass = encrypt_secret(data.password, context.tenant_id)
        enc_conn_str = encrypt_secret(data.connection_string, context.tenant_id)

        conn = DatabaseConnection(
            tenant_id=context.tenant_id,
            created_by=context.user_id,
            name=data.name,
            database_type=data.database_type.lower(),
            host=data.host,
            port=data.port,
            database_name=data.database_name,
            username=data.username,
            encrypted_password=enc_pass,
            encrypted_connection_string=enc_conn_str,
            ssl_enabled=data.ssl_enabled,
            ssl_settings=data.ssl_settings,
            connection_options=data.connection_options,
            status="pending",
            schema_sync_status="pending",
            is_active=True,
        )

        created = self.repo.create(conn)
        return DatabaseConnectionResponse.model_validate(created)

    def update_connection(
        self,
        context: TenantContext,
        connection_id: UUID,
        data: DatabaseConnectionUpdate,
    ) -> DatabaseConnectionResponse | None:
        """Update connection settings and re-encrypt secrets, resetting test/sync status."""
        conn = self.repo.get_by_id(context.tenant_id, connection_id)
        if not conn:
            return None

        # SSRF validation
        validate_host_ssrf(data.host)

        conn.name = data.name
        conn.host = data.host
        conn.port = data.port
        conn.database_name = data.database_name
        conn.username = data.username

        if data.password is not None:
            conn.encrypted_password = encrypt_secret(data.password, context.tenant_id)
        if data.connection_string is not None:
            conn.encrypted_connection_string = encrypt_secret(data.connection_string, context.tenant_id)

        conn.ssl_enabled = data.ssl_enabled
        conn.ssl_settings = data.ssl_settings
        conn.connection_options = data.connection_options
        conn.is_active = data.is_active

        # Reset status on edit
        conn.status = "pending"
        conn.schema_sync_status = "pending"

        self.session.flush()
        return DatabaseConnectionResponse.model_validate(conn)

    def delete_connection(self, tenant_id: UUID, connection_id: UUID) -> bool:
        """Delete connection from platform database."""
        return self.repo.delete(tenant_id, connection_id)

    def test_connection(self, context: TenantContext, connection_id: UUID) -> ConnectionTestResponse:
        """Perform read-only connectivity test and update last_tested_at status."""
        conn = self.repo.get_by_id(context.tenant_id, connection_id)
        if not conn:
            raise ValueError("Connection not found.")

        # Decrypt password and connection_string in memory only
        plain_password = decrypt_secret(conn.encrypted_password, context.tenant_id)
        plain_conn_str = decrypt_secret(conn.encrypted_connection_string, context.tenant_id)

        adapter = get_source_adapter(
            database_type=conn.database_type,
            host=conn.host,
            port=conn.port,
            database_name=conn.database_name,
            username=conn.username,
            password=plain_password,
            connection_string=plain_conn_str,
            ssl_enabled=conn.ssl_enabled,
            ssl_settings=conn.ssl_settings,
            connection_options=conn.connection_options,
        )

        success, message = adapter.test_connection(timeout_seconds=5)
        new_status = "healthy" if success else "failed"
        now = datetime.now(timezone.utc)

        self.repo.update_test_status(
            tenant_id=context.tenant_id,
            connection_id=connection_id,
            status=new_status,
            message=message,
            tested_at=now,
        )

        return ConnectionTestResponse(
            connection_id=conn.id,
            status=new_status,
            message=message,
            tested_at=now,
        )
