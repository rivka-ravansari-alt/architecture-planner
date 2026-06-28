"""Resolve GCP billing services by exact catalog display name."""

from __future__ import annotations

from typing import Any


class GcpBillingServiceResolver:
    def __init__(self, services: list[dict[str, Any]]) -> None:
        self._by_display_name = {
            str(service.get("displayName", "")).casefold(): service
            for service in services
            if service.get("displayName")
        }

    def resolve(self, service_name: str) -> dict[str, Any] | None:
        return self._by_display_name.get(service_name.casefold())
