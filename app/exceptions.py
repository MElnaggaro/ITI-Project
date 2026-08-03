"""Stable application errors and safe HTTP translation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request, status
from fastapi.responses import JSONResponse


@dataclass(slots=True)
class ApplicationError(Exception):
    """A public-safe error with protected internal context excluded by design."""

    code: str
    public_message: str
    status_code: int = status.HTTP_400_BAD_REQUEST


class ConfigurationError(ApplicationError):
    """Raised when startup configuration violates a safe invariant."""


class FeatureNotReadyError(ApplicationError):
    """Raised by deliberate Phase 01 interfaces that later phases own."""


async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """Return a stable error body without implementation details."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.public_message,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )
