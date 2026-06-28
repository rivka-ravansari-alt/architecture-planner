"""Normalize Azure Retail Prices items into azure_catalog documents."""

from __future__ import annotations

from typing import Any

from app.config.params import MAX_SKU_DESCRIPTION_CHARS, MAX_SKUS_PER_COMPONENT
from app.pricing_ingestion.data.azure_formulas import formula_for_service
from app.pricing_ingestion.models.documents import AzureCatalogRecord
from app.pricing_ingestion.providers.base import CatalogNormalizer
from app.utils.slug import slugify


class AzureCatalogNormalizer(CatalogNormalizer):
    def normalize_service(
        self,
        *,
        service: dict[str, Any],
        skus: list[dict[str, Any]],
    ) -> AzureCatalogRecord | None:
        service_id = str(service.get("serviceId", ""))
        display_name = str(service.get("displayName", "")).strip()
        if not service_id or not display_name:
            return None

        sku_map: dict[str, dict[str, Any]] = {}
        seen_roles: set[str] = set()

        for item in self._select_representative_items(skus):
            entry = self._normalize_price_entry(item)
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
        return AzureCatalogRecord(
            id=catalog_id,
            name=display_name,
            skus=sku_map,
            formula=formula_for_service(service_id, list(sku_map.keys())),
        )

    def _select_representative_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not items:
            return []

        primary = [item for item in items if item.get("isPrimaryMeterRegion") is True]
        east_us = [
            item
            for item in items
            if str(item.get("armRegionName", "")).casefold() == "eastus"
        ]

        for bucket in (primary, east_us, items):
            if bucket:
                return bucket
        return items

    def _normalize_price_entry(self, item: dict[str, Any]) -> dict[str, Any] | None:
        meter_id = str(item.get("meterId", ""))
        sku_id = str(item.get("skuId", ""))
        if not meter_id and not sku_id:
            return None

        unit_price = self._extract_unit_price_usd(item)
        if unit_price is None:
            return None

        meter_name = str(item.get("meterName", "")).strip()
        product_name = str(item.get("productName", "")).strip()
        description = meter_name or product_name or sku_id or meter_id
        if len(description) > MAX_SKU_DESCRIPTION_CHARS:
            description = description[: MAX_SKU_DESCRIPTION_CHARS - 3] + "..."

        return {
            "role": self._infer_sku_role(description, item, meter_id or sku_id),
            "sku_id": sku_id or meter_id,
            "meter_id": meter_id,
            "description": description,
            "usage_unit": str(item.get("unitOfMeasure", "")),
            "product_name": product_name,
            "currency": "USD",
            "unit_price_usd": unit_price,
        }

    @staticmethod
    def _extract_unit_price_usd(item: dict[str, Any]) -> float | None:
        for key in ("unitPrice", "retailPrice"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    @staticmethod
    def _infer_sku_role(description: str, item: dict[str, Any], fallback_id: str) -> str:
        lowered = description.lower()
        if "vcpu" in lowered or " cpu" in lowered or lowered.startswith("cpu"):
            return "cpu"
        if "memory" in lowered or "ram" in lowered or "gib" in lowered:
            return "memory"
        if "request" in lowered or "execution" in lowered:
            return "requests" if "execution" not in lowered else "execution"
        if "egress" in lowered or "bandwidth" in lowered or "data transfer" in lowered:
            return "egress"
        if "storage" in lowered or "stored" in lowered or "blob" in lowered:
            return "storage"
        if "queue" in lowered:
            return "queue"
        if "search" in lowered:
            return "search"
        if "token" in lowered:
            return "tokens"

        sku_name = str(item.get("skuName", "")).strip()
        if sku_name:
            return slugify(sku_name, fallback="usage")

        return slugify(fallback_id, fallback="usage")
