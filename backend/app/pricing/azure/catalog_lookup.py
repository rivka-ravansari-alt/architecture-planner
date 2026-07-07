"""Cached Firestore azure_catalog unit price lookup."""

from __future__ import annotations

from typing import Any

from app.pricing.azure.catalog_meter_selector import AzureCatalogMeterSelector
from app.pricing.schemas import CatalogSkuPrice, UsageAssumption
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.utils.slug import slugify


class AzureCatalogLookup:
    """Read unit prices from Firestore azure_catalog documents."""

    def __init__(
        self,
        catalog_repo: AzureCatalogRepository,
        *,
        meter_selector: AzureCatalogMeterSelector | None = None,
    ) -> None:
        self._catalog_repo = catalog_repo
        self._meter_selector = meter_selector or AzureCatalogMeterSelector()
        self._cache: dict[str, dict[str, Any] | None] = {}

    def get_catalog(self, catalog_service_name: str) -> dict[str, Any] | None:
        """Load a catalog document by display name (slugified doc id)."""
        cache_key = catalog_service_name.strip().casefold()
        if cache_key in self._cache:
            return self._cache[cache_key]

        doc = self._catalog_repo.get(slugify(catalog_service_name))
        if doc is None or not doc.get("skus"):
            doc = self._find_by_name(catalog_service_name)

        self._cache[cache_key] = doc
        return doc

    def get_unit_price(
        self,
        catalog_service_name: str,
        role: str,
        *,
        resolved: list[UsageAssumption] | None = None,
    ) -> CatalogSkuPrice | None:
        """Return unit price for one SKU role, optionally tier-aware."""
        doc = self.get_catalog(catalog_service_name)
        if doc is None:
            return None

        if resolved is not None:
            selected = self._meter_selector.select(doc, role, resolved)
            if selected is not None:
                return selected

        skus = doc.get("skus") or {}
        entry = skus.get(role)
        if not isinstance(entry, dict):
            return None

        unit_price = entry.get("unit_price_usd")
        if not isinstance(unit_price, (int, float)):
            return None

        return CatalogSkuPrice(
            role=role,
            unit_price_usd=float(unit_price),
            usage_unit=str(entry.get("usage_unit", "")),
            description=str(entry.get("description", "")),
            sku_id=str(entry.get("sku_id", "")) or None,
            meter_id=str(entry.get("meter_id", "")) or None,
        )

    def _find_by_name(self, catalog_service_name: str) -> dict[str, Any] | None:
        """Fallback: match document by name field when slug id differs."""
        target = catalog_service_name.strip().casefold()
        for service_name in self._catalog_repo.list_enabled_service_names():
            if service_name.casefold() == target:
                return self._catalog_repo.get(slugify(service_name))
        return None
