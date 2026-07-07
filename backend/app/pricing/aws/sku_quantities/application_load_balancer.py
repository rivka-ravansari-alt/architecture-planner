"""Application Load Balancer SKU quantity formulas."""

from __future__ import annotations

from app.pricing.aws.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import AwsServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["hours_per_month", "lcu_hours_per_month"]


def calculate_alb_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=_REQUIRED_KEYS)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    assumption_map = assumptions_by_key(resolved)
    hours = numeric_value(assumption_map, "hours_per_month")
    lcu_hours = numeric_value(assumption_map, "lcu_hours_per_month")
    egress = optional_numeric(assumption_map, "data_egress_gb", 0)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="lb_hours",
            quantity=float(hours),
            unit="hours/month",
            formula="hours_per_month",
            assumption_map=assumption_map,
            input_keys=["hours_per_month"],
        ),
        make_quantity(
            sku_key="lcu_hours",
            quantity=float(lcu_hours),
            unit="LCU-hours/month",
            formula="lcu_hours_per_month",
            assumption_map=assumption_map,
            input_keys=["lcu_hours_per_month"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(egress),
            unit="GB/month",
            formula="data_egress_gb",
            assumption_map=assumption_map,
            input_keys=["data_egress_gb"],
        ),
    ]
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)
