"""Authentication endpoints for login, refresh, and user profile resolution."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_tenant_context, get_db
from core.tenant_context import TenantContext
from schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserMeResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    request_body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with tenant code, email, and password."""
    client_ip = request.client.host if request.client else "unknown"
    service = AuthService(db)
    return service.login(request_body, client_ip=client_ip)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request_body: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Rotate refresh token and issue new token pair."""
    service = AuthService(db)
    return service.refresh(request_body)


@router.get("/me", response_model=UserMeResponse)
def get_me(
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db),
) -> UserMeResponse:
    """Return authenticated user identity and tenant metadata using trusted TenantContext."""
    service = AuthService(db)
    return service.get_user_me(context.tenant_id, context.user_id)
