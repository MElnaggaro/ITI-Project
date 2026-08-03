"""Authentication route boundary; endpoint behavior is implemented in Phase 03."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
