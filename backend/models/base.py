"""Declarative base and metadata configuration for Section 7 application models."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Section 7 constraint naming convention
POSTGRES_NAMING_CONVENTION = {
    "ix": "idx_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "chk_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Shared SQLAlchemy metadata for the platform database schema."""

    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)
