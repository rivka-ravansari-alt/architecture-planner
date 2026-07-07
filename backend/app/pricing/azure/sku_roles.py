"""Resolve calculator sku_key values to Firestore catalog SKU roles."""

from __future__ import annotations

from app.pricing.schemas import AzureServicePricingModel

# Calculator sku_key -> catalog role(s) when definition key or roles differ.
_SKU_ROLE_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "Azure Functions": {
        "execution_time_gb_seconds": ["memory"],
        "network_egress_gb": ["egress"],
        "vcpu_hours": ["cpu"],
    },
    "Azure Blob Storage": {
        "storage_gb_month": ["storage"],
        "write_operations": ["requests"],
        "read_operations": ["requests"],
        "list_operations": ["requests"],
        "retrieval_gb": ["egress"],
        "network_egress_gb": ["egress"],
    },
    "Azure Queue Storage": {
        "storage_gb_month": ["storage"],
        "network_egress_gb": ["egress"],
    },
    "Azure Container Apps": {
        "network_egress_gb": ["egress"],
    },
    "Azure Service Bus": {
        "operations": ["queue"],
        "brokered_connections": ["requests"],
        "messaging_unit_hours": ["cpu"],
        "network_egress_gb": ["egress"],
        "base_units_month": ["namespace"],
    },
    "Azure SQL Database": {
        "storage_gb_month": ["storage"],
        "backup_storage_gb_month": ["storage"],
        "database_instance_months": ["instance"],
    },
}

# SKUs with no catalog role mapping (warn and skip).
_UNPRICED_SKU_KEYS: dict[str, frozenset[str]] = {}


class SkuRoleResolver:
    """Map calculator sku_key values to azure_catalog SKU role keys."""

    def __init__(
        self,
        *,
        role_overrides: dict[str, dict[str, list[str]]] | None = None,
        unpriced_sku_keys: dict[str, frozenset[str]] | None = None,
    ) -> None:
        self._role_overrides = role_overrides or _SKU_ROLE_OVERRIDES
        self._unpriced_sku_keys = unpriced_sku_keys or _UNPRICED_SKU_KEYS

    def resolve(self, model: AzureServicePricingModel, sku_key: str) -> list[str]:
        """Return catalog role(s) for a calculator sku_key, or empty if unpriced in v1."""
        if sku_key in self._unpriced_sku_keys.get(model.service, frozenset()):
            return []

        service_overrides = self._role_overrides.get(model.service, {})
        if sku_key in service_overrides:
            return list(service_overrides[sku_key])

        sku_defs = {item.key: item for item in model.pricing_model.calculated_skus}
        if sku_key in sku_defs:
            return list(sku_defs[sku_key].catalog_sku_roles)

        # Alias common calculator keys to definition keys.
        aliases = {
            "storage_gb_month": "storage_gb_months",
            "backup_storage_gb_month": "backup_storage_gb_months",
            "network_egress_gb": "egress_gb",
            "execution_time_gb_seconds": "gb_seconds",
        }
        alias_key = aliases.get(sku_key)
        if alias_key and alias_key in sku_defs:
            return list(sku_defs[alias_key].catalog_sku_roles)

        return []

    def is_unpriced_sku(self, model: AzureServicePricingModel, sku_key: str) -> bool:
        return sku_key in self._unpriced_sku_keys.get(model.service, frozenset())
