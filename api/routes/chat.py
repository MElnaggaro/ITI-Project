"""Chat route boundary; behavior is implemented in Phases 15 and 18."""

from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])
