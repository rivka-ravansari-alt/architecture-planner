"""Normalize AWS Price List products into aws_catalog documents."""

from __future__ import annotations

from typing import Any

from app.config.params import MAX_SKU_DESCRIPTION_CHARS, MAX_SKUS_PER_COMPONENT
from app.pricing_ingestion.data.aws_formulas import formula_for_service
from app.pricing_ingestion.models.documents import AwsCatalogRecord
from app.pricing_ingestion.providers.base import CatalogNormalizer
from app.utils.slug import slugify


class AwsCatalogNormalizer(CatalogNormalizer):
    def normalize_service(
        self,
        *,
        service: dict[str, Any],
        skus: list[dict[str, Any]],
    ) -> AwsCatalogRecord | None:
        service_code = str(service.get("serviceCode", service.get("serviceId", "")))
        display_name = str(service.get("displayName", "")).strip()
        if not service_code or not display_name:
            return None

        sku_map: dict[str, dict[str, Any]] = {}
        seen_roles: set[str] = set()

        for item in skus:
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
        return AwsCatalogRecord(
            id=catalog_id,
            name=display_name,
            skus=sku_map,
            formula=formula_for_service(service_code, list(sku_map.keys())),
        )

    def _normalize_price_entry(self, item: dict[str, Any]) -> dict[str, Any] | None:
        sku = str(item.get("sku", ""))
        if not sku:
            return None

        price_dimension = item.get("priceDimension") or {}
        unit_price = self._extract_unit_price_usd(price_dimension)
        if unit_price is None:
            return None

        attributes = item.get("attributes") or {}
        description = str(price_dimension.get("description", "")).strip()
        if not description:
            description = str(attributes.get("groupDescription") or attributes.get("usagetype") or sku)
        if len(description) > MAX_SKU_DESCRIPTION_CHARS:
            description = description[: MAX_SKU_DESCRIPTION_CHARS - 3] + "..."

        return {
            "role": self._infer_sku_role(description, attributes, sku),
            "sku_id": sku,
            "description": description,
            "usage_unit": str(price_dimension.get("unit", "")),
            "product_family": str(item.get("productFamily", "")),
            "currency": "USD",
            "unit_price_usd": unit_price,
            "effective_date": str(item.get("effectiveDate", "")),
        }

    @staticmethod
    def _extract_unit_price_usd(price_dimension: dict[str, Any]) -> float | None:
        unit_prices = price_dimension.get("pricePerUnit") or {}
        value = unit_prices.get("USD")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _infer_sku_role(description: str, attributes: dict[str, Any], sku: str) -> str:
        lowered = description.lower()
        group = str(attributes.get("group") or attributes.get("groupDescription") or "").lower()
        usage_type = str(attributes.get("usagetype", "")).lower()
        combined = f"{lowered} {group} {usage_type}"

        if "request" in combined:
            return "requests"
        if "duration" in combined or "gb-second" in combined or "lambda" in group:
            return "duration"
        if "vcpu" in combined or " cpu" in combined:
            return "cpu"
        if "memory" in combined or " ram" in combined:
            return "memory"
        if "storage" in combined or "stored" in combined:
            return "storage"
        if "data transfer" in combined or "egress" in combined:
            return "egress"
        if "alarm" in combined:
            return "alarms"

        if group:
            return slugify(group, fallback="usage")
        if usage_type:
            return slugify(usage_type, fallback="usage")
        return slugify(sku, fallback="usage")
