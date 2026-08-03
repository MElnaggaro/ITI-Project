"""File route boundary; behavior is implemented in Phases 11 and 12."""

from fastapi import APIRouter

router = APIRouter(prefix="/files", tags=["files"])
