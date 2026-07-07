"""Select the best-matching catalog meter for resolved usage assumptions."""

from __future__ import annotations

from typing import Any

from app.pricing.schemas import CatalogSkuPrice, UsageAssumption


class AzureCatalogMeterSelector:
    """Pick a catalog SKU entry using tier, redundancy, and plan assumptions."""

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
        access_tier = str(assumption_map.get("access_tier", "Hot")).strip().casefold()
        redundancy = str(assumption_map.get("redundancy", "LRS")).strip().casefold()
        tier = str(assumption_map.get("tier", "")).strip().casefold()
        messaging_tier = str(assumption_map.get("messaging_tier", "")).strip().casefold()

        keys: list[str] = []
        if role == "storage" and access_tier and redundancy:
            keys.append(f"storage:{access_tier}:{redundancy}")
            keys.append(f"storage_{access_tier}_{redundancy}")
        if role == "instance" and tier:
            tier_slug = tier.replace(" ", "_")
            keys.append(f"instance:{tier_slug}")
            keys.append(f"instance:{tier}")
            keys.append(f"instance_{tier_slug}")
        if role == "namespace" and messaging_tier:
            keys.append(f"namespace:{messaging_tier}")
            keys.append(f"namespace_{messaging_tier}")
        keys.append(role)
        return [key for key in keys if key in skus]

    @staticmethod
    def _entry_matches(compound_key: str, assumption_map: dict[str, Any]) -> bool:
        parts = compound_key.split(":")
        if len(parts) < 2:
            return True
        role = parts[0]
        if role == "storage" and len(parts) >= 3:
            tier = str(assumption_map.get("access_tier", "hot")).casefold()
            redundancy = str(assumption_map.get("redundancy", "lrs")).casefold()
            return parts[1] == tier and parts[2] == redundancy
        if role == "instance" and len(parts) >= 2:
            tier = str(assumption_map.get("tier", "")).casefold()
            return tier and tier in parts[1].casefold()
        if role == "namespace" and len(parts) >= 2:
            return str(assumption_map.get("messaging_tier", "standard")).casefold() == parts[1]
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
            meter_id=str(entry.get("meter_id", "")) or None,
        )
