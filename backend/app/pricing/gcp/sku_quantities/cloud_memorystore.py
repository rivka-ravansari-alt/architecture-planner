"""Cloud Memorystore for Redis SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["hours_per_month"]


def calculate_cloud_memorystore_quantities(
    model: GcpServicePricingModel,
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
    hours = numeric_value(assumption_map, "hours_per_month")
    data_egress_gb = optional_numeric(assumption_map, "data_egress_gb", 0)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="instance_hours",
            quantity=float(hours),
            unit="hours/month",
            formula="hours_per_month",
            assumption_map=assumption_map,
            input_keys=["hours_per_month", "node_tier"],
        ),
    ]

    if data_egress_gb > 0:
        quantities.append(
            make_quantity(
                sku_key="egress_gb",
                quantity=float(data_egress_gb),
                unit="GB/month",
                formula="data_egress_gb",
                assumption_map=assumption_map,
                input_keys=["data_egress_gb"],
            )
        )

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
