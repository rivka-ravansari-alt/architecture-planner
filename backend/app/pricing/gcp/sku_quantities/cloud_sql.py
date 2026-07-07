"""Cloud SQL SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import (
    GcpServicePricingModel,
    IncludedUsage,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)

_REQUIRED_KEYS = ["instance_tier", "storage_gb", "hours_per_month"]

_FREE_TIER_INCLUDED_STORAGE_GB = 10.0


def calculate_cloud_sql_quantities(
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
    hours_per_month = numeric_value(assumption_map, "hours_per_month")
    storage_gb = numeric_value(assumption_map, "storage_gb")
    backup_storage_gb = optional_numeric(assumption_map, "backup_storage_gb", 0)

    billable_storage_gb = max(0.0, float(storage_gb) - _FREE_TIER_INCLUDED_STORAGE_GB)

    included_usage: list[IncludedUsage] = [
        IncludedUsage(
            sku_key="storage_gb_month",
            quantity=_FREE_TIER_INCLUDED_STORAGE_GB,
            unit="GB-months",
            description="Storage included in GCP Free Tier for eligible instance tiers.",
            source="tier",
        )
    ]

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="instance_hours",
            quantity=float(hours_per_month),
            unit="instance-hours/month",
            formula="hours_per_month",
            assumption_map=assumption_map,
            input_keys=["hours_per_month", "instance_tier"],
        ),
        make_quantity(
            sku_key="storage_gb_month",
            quantity=billable_storage_gb,
            unit="GB-months",
            formula="max(0, storage_gb - free_tier_included)",
            assumption_map=assumption_map,
            input_keys=["storage_gb"],
            raw_quantity=float(storage_gb),
            notes=[f"Free tier included storage: {_FREE_TIER_INCLUDED_STORAGE_GB} GB."],
        ),
    ]

    if backup_storage_gb > 0:
        quantities.append(
            make_quantity(
                sku_key="backup_storage_gb_month",
                quantity=float(backup_storage_gb),
                unit="GB-months",
                formula="backup_storage_gb",
                assumption_map=assumption_map,
                input_keys=["backup_storage_gb"],
            )
        )

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        included_usage=included_usage,
        ready=True,
    )
