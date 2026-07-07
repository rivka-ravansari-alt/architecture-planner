"""Azure SQL Database SKU quantity formulas."""

from __future__ import annotations

from app.pricing.azure.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
    string_value,
)
from app.pricing.schemas import (
    AzureServicePricingModel,
    IncludedUsage,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)

_REQUIRED_KEYS = ["tier", "storage_gb"]

# Included storage by tier label (case-insensitive substring match).
_TIER_INCLUDED_STORAGE_GB: tuple[tuple[str, float], ...] = (
    ("basic", 2),
    ("standard s0", 250),
    ("standard s1", 250),
    ("standard s2", 250),
    ("standard s3", 250),
    ("standard s4", 250),
    ("standard s6", 250),
    ("standard s7", 250),
    ("standard s9", 250),
    ("standard s12", 250),
    ("premium p1", 500),
    ("premium p2", 500),
    ("premium p4", 500),
    ("premium p6", 500),
    ("premium p11", 500),
    ("premium p15", 500),
)


def _included_storage_gb_for_tier(tier: str) -> float:
    normalized = tier.strip().casefold()
    for label, included_gb in _TIER_INCLUDED_STORAGE_GB:
        if label in normalized:
            return included_gb
    return 0.0


def calculate_sql_database_quantities(
    model: AzureServicePricingModel,
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
    tier = string_value(assumption_map, "tier")
    storage_gb = numeric_value(assumption_map, "storage_gb")
    backup_storage_gb = optional_numeric(assumption_map, "backup_storage_gb", 0)

    included_storage_gb = _included_storage_gb_for_tier(tier)
    billable_storage_gb = max(0.0, float(storage_gb) - included_storage_gb)

    included_usage: list[IncludedUsage] = []
    if included_storage_gb > 0:
        included_usage.append(
            IncludedUsage(
                sku_key="storage_gb_month",
                quantity=included_storage_gb,
                unit="GB-months",
                description=f"Storage included in {tier!r} tier selection.",
                source="tier",
            )
        )
    elif included_storage_gb == 0:
        included_usage.append(
            IncludedUsage(
                sku_key="storage_gb_month",
                quantity=0,
                unit="GB-months",
                description=(
                    f"No included storage mapped for tier {tier!r}; "
                    "all allocated storage is billable."
                ),
                source="tier",
            )
        )

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="database_instance_months",
            quantity=1.0,
            unit="instance-months",
            formula="1",
            assumption_map=assumption_map,
            input_keys=["tier"],
            notes=[
                "Flat instance-month count; tier pricing comes from catalog, not dynamic vCore math."
            ],
        ),
        make_quantity(
            sku_key="storage_gb_month",
            quantity=billable_storage_gb,
            unit="GB-months",
            formula="max(0, storage_gb - included_storage_gb_for_tier)",
            assumption_map=assumption_map,
            input_keys=["storage_gb", "tier"],
            raw_quantity=float(storage_gb),
            notes=[
                f"Included storage for tier: {included_storage_gb} GB.",
            ],
            warnings=(
                ["Allocated storage exceeds tier-included allowance; overage is billable."]
                if billable_storage_gb > 0 and included_storage_gb > 0
                else []
            ),
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
                notes=["Long-term backup retention beyond tier-included backup storage."],
            )
        )

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        included_usage=included_usage,
        ready=True,
    )
