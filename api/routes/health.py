"""Safe operational health and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import get_app_settings, get_db
from services.observability_service import get_system_health

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Overall system health check")
def health_check(db: Session = Depends(get_db)) -> dict[str, object]:
    """Report overall platform operational status."""
    return get_system_health(db)


@router.get("/live", summary="Process liveness")
async def liveness(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, object]:
    """Report process liveness without probing or exposing dependencies."""

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_environment,
    }


@router.get("/ready", summary="Foundation readiness")
async def readiness(
    response: Response,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, object]:
    """Expose configuration readiness."""

    response.status_code = status.HTTP_200_OK
    return {
        "status": "ready",
        "checks": {
            "configuration": "ok",
            "dependencies": "deferred_to_owning_phases",
        },
        "environment": settings.app_environment,
    }
