"""Authentication route definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.api.controllers.auth_controller import AuthController
from app.core.dependencies import get_auth_service, get_optional_user
from app.models import User
from app.schemas.auth import UserOut
from app.services.auth_service import AuthService


def _controller(auth_service: AuthService = Depends(get_auth_service)) -> AuthController:
    return AuthController(auth_service)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login(request: Request, controller: AuthController = Depends(_controller)):
    return await controller.google_login(request)


@router.get("/google/callback")
async def google_callback(request: Request, controller: AuthController = Depends(_controller)):
    return await controller.google_callback(request)


@router.get("/me", response_model=UserOut | None)
def auth_me(
    user: User | None = Depends(get_optional_user),
    controller: AuthController = Depends(_controller),
):
    if user is None:
        return None
    return controller.current_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(controller: AuthController = Depends(_controller)):
    return controller.logout()
