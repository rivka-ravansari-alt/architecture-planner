"""Health check HTTP controller."""

from __future__ import annotations

from app.config.settings import settings


class HealthController:
    def check(self) -> dict[str, str | bool]:
        return {
            "status": "ok",
            "use_static_ai_response": settings.use_static_ai_response,
            "openai_configured": bool(settings.openai_api_key),
        }
