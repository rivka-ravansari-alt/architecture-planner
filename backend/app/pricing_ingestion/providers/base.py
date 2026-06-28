"""Abstract base classes for multi-cloud pricing ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.pricing_ingestion.schemas.sync import ProviderPricingSyncResponse


class BillingClient(ABC):
    """Fetches raw pricing catalog data from a cloud billing API."""

    @abstractmethod
    def list_services(self) -> list[dict[str, Any]]:
        """Return all billable services/products from the provider catalog."""

    @abstractmethod
    def list_skus_for_service(self, service_id: str) -> list[dict[str, Any]]:
        """Return SKUs/prices for a single service/product."""


class CatalogNormalizer(ABC):
    """Transforms provider-specific billing payloads into Firestore catalog records."""

    @abstractmethod
    def normalize_service(
        self,
        *,
        service: dict[str, Any],
        skus: list[dict[str, Any]],
    ) -> Any | None:
        """Normalize one service and its SKUs into a catalog document, or None if unusable."""


class PricingSyncService(ABC):
    """Orchestrates pricing sync for a single cloud provider."""

    provider: ClassVar[str]

    @abstractmethod
    def sync(self, *, triggered_by: str | None = None) -> ProviderPricingSyncResponse:
        """Run a full pricing sync for this provider."""
