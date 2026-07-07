"""Resolve calculator sku_key values to Firestore gcp_catalog SKU roles."""

from __future__ import annotations

from app.pricing.schemas import GcpServicePricingModel

_SKU_ROLE_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "Cloud Run Functions": {
        "gb_seconds": ["cpu", "memory"],
    },
    "Cloud Run": {
        "vcpu_hours": ["cpu"],
        "memory_gb_hours": ["memory"],
    },
    "Cloud SQL": {
        "instance_hours": ["cpu"],
        "storage_gb_month": ["storage"],
        "backup_storage_gb_month": ["storage"],
    },
    "Cloud Firestore": {
        "storage_gb_month": ["storage"],
        "read_requests": ["requests"],
        "write_requests": ["requests"],
        "delete_requests": ["requests"],
    },
    "Cloud Storage": {
        "storage_gb_month": ["storage"],
    },
    "Cloud Pub/Sub": {},
    "Cloud Tasks": {
        "storage_gb_month": ["storage"],
    },
    "Cloud Memorystore for Redis": {
        "instance_hours": ["cpu"],
    },
    "API Gateway": {},
    "Secret Manager": {
        "secret_months": ["storage"],
    },
    "Networking": {
        "lb_hours": ["cpu"],
    },
    "Firebase": {},
    "Firebase Hosting": {},
    "BigQuery": {
        "data_scanned_tb": ["requests"],
        "storage_gb_month": ["storage"],
    },
    "Cloud Logging": {
        "ingestion_gb": ["requests"],
        "storage_gb_month": ["storage"],
    },
    "Cloud Monitoring": {
        "custom_metrics": ["storage"],
        "alert_policies": ["cpu"],
    },
    "Cloud Trace": {
        "spans_ingested": ["requests"],
        "spans_scanned": ["memory"],
    },
    "Gemini API": {
        "input_tokens": ["requests"],
        "output_tokens": ["memory"],
    },
    "Vertex AI": {
        "input_tokens": ["requests"],
        "output_tokens": ["memory"],
        "prediction_hours": ["cpu"],
    },
    "Vertex AI Search": {
        "storage_gb_month": ["storage"],
    },
}

_UNPRICED_SKU_KEYS: dict[str, frozenset[str]] = {}


class GcpSkuRoleResolver:
    """Map calculator sku_key values to gcp_catalog SKU role keys."""

    def __init__(
        self,
        *,
        role_overrides: dict[str, dict[str, list[str]]] | None = None,
        unpriced_sku_keys: dict[str, frozenset[str]] | None = None,
    ) -> None:
        self._role_overrides = role_overrides or _SKU_ROLE_OVERRIDES
        self._unpriced_sku_keys = unpriced_sku_keys or _UNPRICED_SKU_KEYS

    def resolve(self, model: GcpServicePricingModel, sku_key: str) -> list[str]:
        if sku_key in self._unpriced_sku_keys.get(model.service, frozenset()):
            return []

        service_overrides = self._role_overrides.get(model.service, {})
        if sku_key in service_overrides:
            return list(service_overrides[sku_key])

        sku_defs = {item.key: item for item in model.pricing_model.calculated_skus}
        if sku_key in sku_defs:
            return list(sku_defs[sku_key].catalog_sku_roles)

        aliases = {
            "network_egress_gb": "egress_gb",
        }
        alias_key = aliases.get(sku_key)
        if alias_key and alias_key in sku_defs:
            return list(sku_defs[alias_key].catalog_sku_roles)

        return []

    def is_unpriced_sku(self, model: GcpServicePricingModel, sku_key: str) -> bool:
        return sku_key in self._unpriced_sku_keys.get(model.service, frozenset())
