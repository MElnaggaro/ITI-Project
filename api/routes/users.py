"""User administration extension boundary; behavior is deferred."""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])
