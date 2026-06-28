"""Factory for cloud pricing sync services."""

from __future__ import annotations

from app.config.params import PRICING_PROVIDERS
from app.pricing_ingestion.providers.base import PricingSyncService


class PricingSyncRegistry:
    def __init__(self, services: dict[str, PricingSyncService]) -> None:
        missing = set(PRICING_PROVIDERS) - set(services)
        if missing:
            raise ValueError(f"Missing pricing sync services for providers: {sorted(missing)}")
        self._services = services

    def get(self, provider: str) -> PricingSyncService:
        try:
            return self._services[provider]
        except KeyError as exc:
            raise ValueError(f"Unsupported pricing provider: {provider}") from exc

    def all(self) -> list[PricingSyncService]:
        return [self._services[provider] for provider in PRICING_PROVIDERS]
