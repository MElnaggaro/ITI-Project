"""Safe operational health endpoints available during Phase 01."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.config import Settings
from app.dependencies import get_app_settings

router = APIRouter(prefix="/health", tags=["health"])


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
    """Expose only configuration readiness; real dependency probes arrive later."""

    response.status_code = status.HTTP_200_OK
    return {
        "status": "ready",
        "checks": {
            "configuration": "ok",
            "dependencies": "deferred_to_owning_phases",
        },
        "environment": settings.app_environment,
    }
