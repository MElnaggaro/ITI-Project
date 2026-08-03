"""Baseline permission-management extension boundary; behavior is deferred."""

from fastapi import APIRouter

router = APIRouter(prefix="/permissions", tags=["permissions"])
