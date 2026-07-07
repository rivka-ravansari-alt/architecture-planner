"""Secret Manager SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS: list[str] = []


def calculate_secret_manager_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    assumption_map = assumptions_by_key(resolved)
    secrets = optional_numeric(assumption_map, "secrets_count", 1)
    api_calls = optional_numeric(assumption_map, "api_calls_per_month", 0)

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
