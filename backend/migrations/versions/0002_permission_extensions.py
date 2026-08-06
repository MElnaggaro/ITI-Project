"""0002_permission_extensions

Revision ID: 0002_permission_extensions
Revises: 0001_initial_schema
Create Date: 2026-08-03 01:00:00.000000

"""

from __future__ import annotations

import alembic.op as op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_permission_extensions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Partial unique index for direct user table grants
    op.create_index(
        "idx_table_permissions_user_grant",
        "table_permissions",
        ["user_id", "connection_id", "table_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
        sqlite_where=sa.text("user_id IS NOT NULL"),
    )

    # Partial unique index for role table grants
    op.create_index(
        "idx_table_permissions_role_grant",
        "table_permissions",
        ["role_id", "connection_id", "table_id"],
        unique=True,
        postgresql_where=sa.text("role_id IS NOT NULL"),
        sqlite_where=sa.text("role_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_table_permissions_role_grant", table_name="table_permissions")
    op.drop_index("idx_table_permissions_user_grant", table_name="table_permissions")
