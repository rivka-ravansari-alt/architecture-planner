"""Normalize Google Cloud Billing SKUs into gcp_catalog documents."""

from __future__ import annotations

from typing import Any

from app.config.params import MAX_SKU_DESCRIPTION_CHARS, MAX_SKUS_PER_COMPONENT
from app.pricing_ingestion.data.formulas import formula_for_service
from app.pricing_ingestion.models.documents import GcpCatalogRecord
from app.pricing_ingestion.providers.base import CatalogNormalizer
from app.utils.slug import slugify


class GcpCatalogNormalizer(CatalogNormalizer):
    def normalize_service(
        self,
        *,
        service: dict[str, Any],
        skus: list[dict[str, Any]],
    ) -> GcpCatalogRecord | None:
        service_id = str(service.get("serviceId", ""))
        display_name = str(service.get("displayName", "")).strip()
        if not service_id or not display_name:
            return None

        sku_map: dict[str, dict[str, Any]] = {}
        seen_roles: set[str] = set()

        for sku in skus:
            entry = self._normalize_sku_entry(sku)
            if entry is None:
                continue

            role = entry["role"]
            if role in seen_roles:
                continue
            seen_roles.add(role)

            if len(sku_map) >= MAX_SKUS_PER_COMPONENT:
                break

            sku_map[role] = {key: value for key, value in entry.items() if key != "role"}

        if not sku_map:
            return None

        catalog_id = slugify(display_name)
        return GcpCatalogRecord(
            id=catalog_id,
            name=display_name,
            skus=sku_map,
            formula=formula_for_service(service_id, list(sku_map.keys())),
        )

    def _normalize_sku_entry(self, sku: dict[str, Any]) -> dict[str, Any] | None:
        sku_id = str(sku.get("skuId", ""))
        if not sku_id:
            return None

        pricing_info = sku.get("pricingInfo") or []
        if not pricing_info:
            return None

        expression = pricing_info[0].get("pricingExpression") or {}
        unit_price = self._extract_unit_price_usd(pricing_info[0])
        if unit_price is None:
            return None

        category = sku.get("category") or {}
        description = str(sku.get("description", sku_id))
        if len(description) > MAX_SKU_DESCRIPTION_CHARS:
            description = description[: MAX_SKU_DESCRIPTION_CHARS - 3] + "..."

        return {
            "role": self._infer_sku_role(description, category, sku_id),
            "sku_id": sku_id,
            "description": description,
            "usage_unit": str(expression.get("usageUnit", "")),
            "base_unit": str(expression.get("baseUnit", "")),
            "currency": "USD",
            "unit_price_usd": unit_price,
        }

    @staticmethod
    def _extract_unit_price_usd(pricing_info: dict[str, Any]) -> float | None:
        expression = pricing_info.get("pricingExpression") or {}
        tiered_rates = expression.get("tieredRates") or []
        if not tiered_rates:
            return None

        unit_price = tiered_rates[0].get("unitPrice") or {}
        units = int(unit_price.get("units", 0) or 0)
        nanos = int(unit_price.get("nanos", 0) or 0)
        return units + nanos / 1_000_000_000

    @staticmethod
    def _infer_sku_role(description: str, category: dict[str, Any], sku_id: str) -> str:
        lowered = description.lower()
        if "cpu" in lowered:
            return "cpu"
        if "memory" in lowered or "ram" in lowered:
            return "memory"
        if "request" in lowered:
            return "requests"
        if "egress" in lowered:
            return "egress"
        if "storage" in lowered:
            return "storage"

        usage_type = str(category.get("usageType", "")).strip()
        resource_group = str(category.get("resourceGroup", "")).strip()
        if resource_group and usage_type:
            return slugify(f"{resource_group}_{usage_type}", fallback="usage")
        if usage_type:
            return slugify(usage_type, fallback="usage")
        if resource_group:
            return slugify(resource_group, fallback="usage")

        return slugify(sku_id, fallback="usage")
