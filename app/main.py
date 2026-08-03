"""FastAPI process entry point for the Phase 01 foundation."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.router import api_router
from app.config import get_settings
from app.exceptions import ApplicationError, application_error_handler
from app.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure safe process concerns; feature services are added by later phases."""

    settings = get_settings()
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info(
        "application_started",
        extra={"structured": settings.safe_summary()},
    )
    yield
    logging.getLogger(__name__).info("application_stopped")


def create_app() -> FastAPI:
    """Create the API shell without enabling future business endpoints."""

    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "health", "description": "Operational health and readiness."},
            {"name": "auth", "description": "Implemented in Phase 03."},
            {"name": "database-connections", "description": "Implemented in Phase 05."},
            {"name": "files", "description": "Implemented in Phase 11."},
            {"name": "chat", "description": "Implemented in Phases 15 and 18."},
        ],
    )

    @application.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get(
            settings.request_id_header,
            str(uuid4()),
        )
        response = await call_next(request)
        response.headers[settings.request_id_header] = request.state.request_id
        return response

    @application.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError):
        return await application_error_handler(request, exc)

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logging.getLogger(__name__).exception(
            "unexpected_application_error",
            extra={"structured": {"request_id": getattr(request.state, "request_id", None)}},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    application.include_router(api_router)
    return application


app = create_app()
