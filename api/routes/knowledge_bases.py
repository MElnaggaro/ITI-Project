"""Knowledge-base route boundary; behavior is implemented in Phase 14."""

from fastapi import APIRouter

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])
