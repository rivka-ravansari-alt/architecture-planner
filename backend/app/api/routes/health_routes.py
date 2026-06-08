"""Health check route definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.controllers.health_controller import HealthController

router = APIRouter(tags=["health"])


def _controller() -> HealthController:
    return HealthController()


@router.get("/health")
async def health(controller: HealthController = Depends(_controller)):
    return controller.check()
