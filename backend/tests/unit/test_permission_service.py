"""Unit tests for permission resolution service and row-filter DSL validation."""

from uuid import uuid4

import pytest

from core.security import hash_password
from repositories.connection_repository import ConnectionRepository
from repositories.permission_repository import PermissionRepository
from repositories.role_repository import RoleRepository
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.permissions import TablePermissionCreate
from services.permission_service import PermissionService, validate_row_filter_dsl


def test_row_filter_dsl_validation():
    """Verify row-filter DSL validator accepts valid structure and rejects invalid operators."""
    # Valid empty filter
    validate_row_filter_dsl({})

    # Valid operator structure
    validate_row_filter_dsl({"department_id": {"eq": 10}})
    validate_row_filter_dsl(
        {
            "and": [
                {"status": {"eq": "active"}},
                {"age": {"gte": 18}},
            ]
        }
    )

    # Invalid operator
    with pytest.raises(ValueError, match="Unsupported row_filter operator"):
        validate_row_filter_dsl({"salary": {"DROP_TABLE": "all"}})

    # Excessive nesting depth
    deep_nested = {"and": [{"and": [{"and": [{"and": [{"and": [{"eq": 1}]}]}]}]}]}
    with pytest.raises(ValueError, match="maximum nesting depth"):
        validate_row_filter_dsl(deep_nested, max_depth=3)


def test_direct_user_grant_precedence(db_session):
    """Assert direct user grant takes precedence over role grants."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)
    role_repo = RoleRepository(db_session)
    perm_repo = PermissionRepository(db_session)
    service = PermissionService(db_session)

    tenant = tenant_repo.create("Test Tenant", "test-tenant")
    user = user_repo.create(tenant.id, "user@test.com", hash_password("pass"))
    role = role_repo.create(tenant.id, "Analyst")
    role_repo.replace_user_roles(tenant.id, user.id, [role.id])

    # Direct user grant with can_read = False
    conn_id = uuid4()
    tbl_id = uuid4()

    # Create dummy connection and table to avoid FK error
    from models.database_connection import DatabaseConnection
    from models.database_table import DatabaseTable
    conn = DatabaseConnection(id=conn_id, tenant_id=tenant.id, name="c1", database_type="postgresql")
    tbl = DatabaseTable(id=tbl_id, tenant_id=tenant.id, connection_id=conn_id, table_name="sales")
    db_session.add_all([conn, tbl])
    db_session.commit()

    # Role grant: can_read = True
    perm_repo.create_table_permission(
        tenant.id,
        TablePermissionCreate(
            connection_id=conn_id,
            table_id=tbl_id,
            role_id=role.id,
            can_read=True,
        ),
    )

    # Direct user grant: can_read = False (Explicit Deny)
    perm_repo.create_table_permission(
        tenant.id,
        TablePermissionCreate(
            connection_id=conn_id,
            table_id=tbl_id,
            user_id=user.id,
            can_read=False,
        ),
    )

    effective = service.resolve_effective_table_permission(tenant.id, user.id, conn_id, tbl_id)
    assert effective.can_read is False, "Direct user deny must override role allow grant."


def test_additive_role_grants(db_session):
    """Assert role grants are additive when no direct user grant exists."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)
    role_repo = RoleRepository(db_session)
    perm_repo = PermissionRepository(db_session)
    service = PermissionService(db_session)

    tenant = tenant_repo.create("Role Tenant", "role-tenant")
    user = user_repo.create(tenant.id, "user2@test.com", hash_password("pass"))
    r1 = role_repo.create(tenant.id, "Role1")
    r2 = role_repo.create(tenant.id, "Role2")
    role_repo.replace_user_roles(tenant.id, user.id, [r1.id, r2.id])

    conn_id = uuid4()
    tbl_id = uuid4()

    from models.database_connection import DatabaseConnection
    from models.database_table import DatabaseTable
    conn = DatabaseConnection(id=conn_id, tenant_id=tenant.id, name="c2", database_type="postgresql")
    tbl = DatabaseTable(id=tbl_id, tenant_id=tenant.id, connection_id=conn_id, table_name="orders")
    db_session.add_all([conn, tbl])
    db_session.commit()

    # r1 grant: filter {region: East}
    perm_repo.create_table_permission(
        tenant.id,
        TablePermissionCreate(
            connection_id=conn_id,
            table_id=tbl_id,
            role_id=r1.id,
            can_read=True,
            row_filter={"region": {"eq": "East"}},
        ),
    )
    # r2 grant: filter {region: West}
    perm_repo.create_table_permission(
        tenant.id,
        TablePermissionCreate(
            connection_id=conn_id,
            table_id=tbl_id,
            role_id=r2.id,
            can_read=True,
            row_filter={"region": {"eq": "West"}},
        ),
    )

    effective = service.resolve_effective_table_permission(tenant.id, user.id, conn_id, tbl_id)
    assert effective.can_read is True
    assert len(effective.effective_row_filters) == 2
