"""Resolve calculator sku_key values to Firestore aws_catalog SKU roles."""

from __future__ import annotations

from app.pricing.schemas import AwsServicePricingModel

_SKU_ROLE_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "Lambda": {
        "gb_seconds": ["duration"],
    },
    "ECS Fargate": {
        "vcpu_hours": ["cpu"],
        "memory_gb_hours": ["memory"],
    },
    "RDS": {
        "instance_hours": ["cpu"],
        "storage_gb_month": ["storage"],
        "backup_storage_gb_month": ["storage"],
    },
    "DynamoDB": {
        "storage_gb_month": ["storage"],
        "read_requests": ["requests"],
        "write_requests": ["requests"],
    },
    "S3": {
        "storage_gb_month": ["storage"],
    },
    "SQS": {},
    "API Gateway": {},
    "SNS": {},
    "CloudFront": {},
    "Application Load Balancer": {
        "lb_hours": ["cpu"],
        "lcu_hours": ["memory"],
    },
    "Secrets Manager": {
        "secret_months": ["storage"],
    },
}

_UNPRICED_SKU_KEYS: dict[str, frozenset[str]] = {}


class AwsSkuRoleResolver:
    """Map calculator sku_key values to aws_catalog SKU role keys."""

    def __init__(
        self,
        *,
        role_overrides: dict[str, dict[str, list[str]]] | None = None,
        unpriced_sku_keys: dict[str, frozenset[str]] | None = None,
    ) -> None:
        self._role_overrides = role_overrides or _SKU_ROLE_OVERRIDES
        self._unpriced_sku_keys = unpriced_sku_keys or _UNPRICED_SKU_KEYS

    def resolve(self, model: AwsServicePricingModel, sku_key: str) -> list[str]:
        if sku_key in self._unpriced_sku_keys.get(model.service, frozenset()):
            return []

        service_overrides = self._role_overrides.get(model.service, {})
        if sku_key in service_overrides:
            return self._filter_roles(list(service_overrides[sku_key]))

        sku_defs = {item.key: item for item in model.pricing_model.calculated_skus}
        if sku_key in sku_defs:
            return self._filter_roles(list(sku_defs[sku_key].catalog_sku_roles))

        aliases = {
            "network_egress_gb": "egress_gb",
        }
        alias_key = aliases.get(sku_key)
        if alias_key and alias_key in sku_defs:
            return self._filter_roles(list(sku_defs[alias_key].catalog_sku_roles))

        return []

    @staticmethod
    def _filter_roles(roles: list[str]) -> list[str]:
        return [role for role in roles if "experimenthour" not in role.casefold()]

    def is_unpriced_sku(self, model: AwsServicePricingModel, sku_key: str) -> bool:
        return sku_key in self._unpriced_sku_keys.get(model.service, frozenset())
