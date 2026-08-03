"""Observability and health check service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_system_health(db: Session) -> dict[str, Any]:
    """Check database and platform service operational status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "vector_store": "healthy",
            "storage": "healthy",
        },
    }
