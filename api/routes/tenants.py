"""Tenant administration extension boundary; behavior is deferred."""

from fastapi import APIRouter

router = APIRouter(prefix="/tenants", tags=["tenants"])
