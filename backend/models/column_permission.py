"""ColumnPermission model mapping Section 7.5 column_permissions table DDL."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ColumnPermission(Base):
    """Column-level granular permissions and masking control."""

    __tablename__ = "column_permissions"

    __table_args__ = (
        UniqueConstraint("table_permission_id", "column_id", name="uq_column_permission"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    table_permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("table_permissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("database_columns.id", ondelete="CASCADE"),
        nullable=False,
    )
    can_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    can_filter: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    can_aggregate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE"),
    )
    mask_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
