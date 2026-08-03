"""Declarative base only; no application tables are declared during Phase 01."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy metadata for the Phase 02 migration."""
