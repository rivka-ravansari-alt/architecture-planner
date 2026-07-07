"""Secrets Manager SKU quantity formulas."""

from __future__ import annotations

from app.pricing.aws.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
)
from app.pricing.schemas import AwsServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["secrets_count", "api_calls_per_month"]


def calculate_secrets_manager_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=_REQUIRED_KEYS)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    assumption_map = assumptions_by_key(resolved)
    secrets = numeric_value(assumption_map, "secrets_count")
    api_calls = numeric_value(assumption_map, "api_calls_per_month")

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="secret_months",
            quantity=float(secrets),
            unit="secret-months",
            formula="secrets_count",
            assumption_map=assumption_map,
            input_keys=["secrets_count"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(api_calls),
            unit="operations/month",
            formula="api_calls_per_month",
            assumption_map=assumption_map,
            input_keys=["api_calls_per_month"],
        ),
    ]
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)
