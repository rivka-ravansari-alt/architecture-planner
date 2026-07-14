"""Health check HTTP controller."""

from __future__ import annotations


class HealthController:
    def check(self) -> dict[str, str]:
        return {"status": "ok"}
