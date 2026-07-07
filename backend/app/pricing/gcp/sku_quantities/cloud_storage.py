"""Cloud Storage SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["storage_gb"]


def calculate_cloud_storage_quantities(
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
    write_operations = optional_numeric(assumption_map, "write_operations", 0)
    read_operations = optional_numeric(assumption_map, "read_operations", 0)
    data_egress_gb = optional_numeric(assumption_map, "data_egress_gb", 0)
    total_requests = float(write_operations) + float(read_operations)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="storage_gb_month",
            quantity=float(storage_gb),
            unit="GB-months",
            formula="storage_gb",
            assumption_map=assumption_map,
            input_keys=["storage_gb", "storage_class"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=total_requests,
            unit="operations/month",
            formula="write_operations + read_operations",
            assumption_map=assumption_map,
            input_keys=["write_operations", "read_operations"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(data_egress_gb),
            unit="GB/month",
            formula="data_egress_gb",
            assumption_map=assumption_map,
            input_keys=["data_egress_gb"],
        ),
    ]

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
