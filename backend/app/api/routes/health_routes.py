"""Health check route definitions."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.controllers.health_controller import HealthController

router = APIRouter(tags=["health"])
_controller = HealthController()


@router.get("/health")
def health():
    return _controller.check()
