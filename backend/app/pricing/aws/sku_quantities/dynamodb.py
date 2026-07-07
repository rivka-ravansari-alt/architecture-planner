"""DynamoDB SKU quantity formulas."""

from __future__ import annotations

from app.pricing.aws.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
)
from app.pricing.schemas import (
    AwsServicePricingModel,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)

_REQUIRED_KEYS = ["storage_gb", "read_requests_per_month", "write_requests_per_month"]


def calculate_dynamodb_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=_REQUIRED_KEYS)
    if missing:
        return SkuQuantityResult(
            service=model.service,
            quantities=[],
            missing=missing,
            ready=False,
        )

    assumption_map = assumptions_by_key(resolved)
    storage_gb = numeric_value(assumption_map, "storage_gb")
    read_requests = numeric_value(assumption_map, "read_requests_per_month")
    write_requests = numeric_value(assumption_map, "write_requests_per_month")

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="storage_gb_month",
            quantity=float(storage_gb),
            unit="GB-months",
            formula="storage_gb",
            assumption_map=assumption_map,
            input_keys=["storage_gb"],
        ),
        make_quantity(
            sku_key="read_requests",
            quantity=float(read_requests),
            unit="requests/month",
            formula="read_requests_per_month",
            assumption_map=assumption_map,
            input_keys=["read_requests_per_month", "billing_mode"],
        ),
        make_quantity(
            sku_key="write_requests",
            quantity=float(write_requests),
            unit="requests/month",
            formula="write_requests_per_month",
            assumption_map=assumption_map,
            input_keys=["write_requests_per_month", "billing_mode"],
        ),
    ]

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
