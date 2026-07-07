"""Select the best-matching GCP catalog meter for resolved usage assumptions."""

from __future__ import annotations

from typing import Any

from app.pricing.schemas import CatalogSkuPrice, UsageAssumption
from app.utils.slug import slugify


class GcpCatalogMeterSelector:
    """Pick a catalog SKU entry using storage class and tier assumptions."""

    def select(
        self,
        catalog_doc: dict[str, Any],
        role: str,
        resolved: list[UsageAssumption],
    ) -> CatalogSkuPrice | None:
        skus = catalog_doc.get("skus") or {}
        if not skus:
            return None

        assumption_map = {item.key: item.value for item in resolved}
        candidates = self._candidate_keys(role, assumption_map, skus)
        for key in candidates:
            entry = skus.get(key)
            if isinstance(entry, dict):
                price = self._to_price(key.split(":")[0] if ":" in key else key, entry)
                if price is not None:
                    return price

        for key, entry in skus.items():
            if not isinstance(entry, dict):
                continue
            if not key.startswith(f"{role}:"):
                continue
            if self._entry_matches(key, assumption_map) and self._to_price(role, entry):
                return self._to_price(role, entry)

        entry = skus.get(role)
        if isinstance(entry, dict):
            return self._to_price(role, entry)
        return None

    def _candidate_keys(
        self,
        role: str,
        assumption_map: dict[str, Any],
        skus: dict[str, Any],
    ) -> list[str]:
        storage_class = str(assumption_map.get("storage_class", "Standard")).strip().casefold()
        instance_tier = str(assumption_map.get("instance_tier", "")).strip().casefold()
        node_tier = str(assumption_map.get("node_tier", "")).strip().casefold()

        keys: list[str] = []
        if role == "storage" and storage_class:
            tier_slug = slugify(storage_class)
            keys.append(f"storage:{tier_slug}")
            keys.append(f"storage_{tier_slug}")
        if role == "cpu" and instance_tier:
            tier_slug = slugify(instance_tier)
            keys.append(f"cpu:{tier_slug}")
            keys.append(f"cpu_{tier_slug}")
        if role == "cpu" and node_tier:
            tier_slug = slugify(node_tier)
            keys.append(f"cpu:{tier_slug}")
            keys.append(f"cpu_{tier_slug}")
        keys.append(role)
        return [key for key in keys if key in skus]

    @staticmethod
    def _entry_matches(compound_key: str, assumption_map: dict[str, Any]) -> bool:
        parts = compound_key.split(":")
        if len(parts) < 2:
            return True
        role = parts[0]
        if role == "storage" and len(parts) >= 2:
            tier = slugify(str(assumption_map.get("storage_class", "standard")))
            return parts[1] == tier
        if role == "cpu" and len(parts) >= 2:
            tier = slugify(
                str(assumption_map.get("instance_tier") or assumption_map.get("node_tier", ""))
            )
            return tier and tier in parts[1].casefold()
        return True

    @staticmethod
    def _to_price(role: str, entry: dict[str, Any]) -> CatalogSkuPrice | None:
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
