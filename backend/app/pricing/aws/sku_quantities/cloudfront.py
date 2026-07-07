"""CloudFront SKU quantity formulas."""

from __future__ import annotations

from app.pricing.aws.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import AwsServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["requests_per_month"]


def calculate_cloudfront_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=_REQUIRED_KEYS)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    assumption_map = assumptions_by_key(resolved)
    requests = numeric_value(assumption_map, "requests_per_month")
    transfer = optional_numeric(assumption_map, "data_transfer_gb", 0)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(transfer),
            unit="GB/month",
            formula="data_transfer_gb",
            assumption_map=assumption_map,
            input_keys=["data_transfer_gb"],
        ),
    ]
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)
