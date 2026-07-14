"""Authentication route definitions (Google OAuth)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.controllers.auth_controller import AuthController
from app.core.dependencies import get_auth_controller, get_optional_user
from app.schemas.auth import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login(
    request: Request,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.google_login(request)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    controller: AuthController = Depends(get_auth_controller),
):
    return await controller.google_callback(request)


@router.get("/me")
def auth_me(
    user: UserOut | None = Depends(get_optional_user),
    controller: AuthController = Depends(get_auth_controller),
) -> UserOut | None:
    return controller.current_user(user)


@router.post("/logout")
def logout(controller: AuthController = Depends(get_auth_controller)):
    return controller.logout()
