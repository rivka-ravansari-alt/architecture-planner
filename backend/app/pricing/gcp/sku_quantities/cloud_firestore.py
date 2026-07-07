"""Cloud Firestore SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["storage_gb", "read_requests_per_month", "write_requests_per_month"]


def calculate_cloud_firestore_quantities(
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
    storage_gb = numeric_value(assumption_map, "storage_gb")
    read_requests = numeric_value(assumption_map, "read_requests_per_month")
    write_requests = numeric_value(assumption_map, "write_requests_per_month")
    delete_requests = optional_numeric(assumption_map, "delete_requests_per_month", 0)

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
            input_keys=["read_requests_per_month"],
        ),
        make_quantity(
            sku_key="write_requests",
            quantity=float(write_requests),
            unit="requests/month",
            formula="write_requests_per_month",
            assumption_map=assumption_map,
            input_keys=["write_requests_per_month"],
        ),
    ]

    if delete_requests > 0:
        quantities.append(
            make_quantity(
                sku_key="delete_requests",
                quantity=float(delete_requests),
                unit="requests/month",
                formula="delete_requests_per_month",
                assumption_map=assumption_map,
                input_keys=["delete_requests_per_month"],
            )
        )

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
