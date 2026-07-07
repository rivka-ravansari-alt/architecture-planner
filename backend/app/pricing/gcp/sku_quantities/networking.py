"""Networking (CDN / load balancer) SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["requests_per_month"]


def calculate_networking_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=_REQUIRED_KEYS)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    assumption_map = assumptions_by_key(resolved)
    requests = numeric_value(assumption_map, "requests_per_month")
    data_transfer = optional_numeric(assumption_map, "data_transfer_gb", 0)
    lb_hours = optional_numeric(assumption_map, "lb_hours_per_month", 730)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month", "networking_mode"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(data_transfer),
            unit="GB/month",
            formula="data_transfer_gb",
            assumption_map=assumption_map,
            input_keys=["data_transfer_gb"],
        ),
    ]

    if lb_hours > 0:
        quantities.append(
            make_quantity(
                sku_key="lb_hours",
                quantity=float(lb_hours),
                unit="hours/month",
                formula="lb_hours_per_month",
                assumption_map=assumption_map,
                input_keys=["lb_hours_per_month", "networking_mode"],
            )
        )

    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)
