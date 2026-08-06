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


class AuthenticationError(ApplicationError):
    """Raised when authentication fails or token is invalid/expired."""

    def __init__(
        self,
        public_message: str = "Authentication failed.",
        code: str = "authentication_failed",
        status_code: int = status.HTTP_401_UNAUTHORIZED,
    ) -> None:
        super().__init__(
            code=code,
            public_message=public_message,
            status_code=status_code,
        )


class AuthorizationError(ApplicationError):
    """Raised when access is denied for an authenticated principal."""

    def __init__(
        self,
        public_message: str = "Access denied.",
        code: str = "access_denied",
        status_code: int = status.HTTP_403_FORBIDDEN,
    ) -> None:
        super().__init__(
            code=code,
            public_message=public_message,
            status_code=status_code,
        )


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        public_message: str = "Resource not found.",
        code: str = "resource_not_found",
        status_code: int = status.HTTP_404_NOT_FOUND,
    ) -> None:
        super().__init__(
            code=code,
            public_message=public_message,
            status_code=status_code,
        )


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
