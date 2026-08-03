"""Conversation route boundary; behavior is implemented in Phase 16."""

from fastapi import APIRouter

router = APIRouter(prefix="/conversations", tags=["conversations"])
