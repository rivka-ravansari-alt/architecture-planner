"""Cached Firestore gcp_catalog unit price lookup."""

from __future__ import annotations

from typing import Any

from app.pricing.gcp.catalog_meter_selector import GcpCatalogMeterSelector
from app.pricing.schemas import CatalogSkuPrice, UsageAssumption
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.utils.slug import slugify


class GcpCatalogLookup:
    """Read unit prices from Firestore gcp_catalog documents."""

    def __init__(
        self,
        catalog_repo: GcpCatalogRepository,
        *,
        meter_selector: GcpCatalogMeterSelector | None = None,
    ) -> None:
        self._catalog_repo = catalog_repo
        self._meter_selector = meter_selector or GcpCatalogMeterSelector()
        self._cache: dict[str, dict[str, Any] | None] = {}

    def get_catalog(self, catalog_service_name: str) -> dict[str, Any] | None:
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
            meter_id=None,
        )

    def _find_by_name(self, catalog_service_name: str) -> dict[str, Any] | None:
        target = catalog_service_name.strip().casefold()
        for service_name in self._catalog_repo.list_enabled_service_names():
            if service_name.casefold() == target:
                return self._catalog_repo.get(slugify(service_name))
        return None
