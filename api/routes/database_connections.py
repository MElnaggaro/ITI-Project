"""Database-connection route boundary; behavior is implemented in Phase 05."""

from fastapi import APIRouter

router = APIRouter(prefix="/database-connections", tags=["database-connections"])
