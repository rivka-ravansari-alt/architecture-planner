"""Azure Service Bus SKU quantity formulas."""

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

_REQUIRED_KEYS = ["messaging_tier", "queue_operations"]

_STANDARD_INCLUDED_CONNECTIONS = 1000


def calculate_service_bus_quantities(
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
    tier = string_value(assumption_map, "messaging_tier").strip().casefold()
    queue_operations = numeric_value(assumption_map, "queue_operations")
    hours_per_month = optional_numeric(assumption_map, "hours_per_month", 730)
    messaging_units = optional_numeric(assumption_map, "messaging_units", 1)
    brokered_connections = int(optional_numeric(assumption_map, "brokered_connections", 0))
    data_egress_gb = optional_numeric(assumption_map, "data_egress_gb", 0)

    quantities: list[SkuQuantity] = []
    included_usage: list[IncludedUsage] = []
    warnings: list[str] = []

    if tier == "premium":
        mu_hours = messaging_units * hours_per_month
        quantities.append(
            make_quantity(
                sku_key="messaging_unit_hours",
                quantity=mu_hours,
                unit="MU-hours/month",
                formula="messaging_units * hours_per_month",
                assumption_map=assumption_map,
                input_keys=["messaging_tier", "messaging_units", "hours_per_month"],
                notes=["Premium tier bills messaging unit capacity hourly."],
            )
        )
    else:
        quantities.append(
            make_quantity(
                sku_key="base_units_month",
                quantity=1.0,
                unit="namespace-months",
                formula="1",
                assumption_map=assumption_map,
                input_keys=["messaging_tier"],
                notes=[f"{tier.title()} tier flat namespace charge."],
            )
        )

    if tier in {"basic", "standard"}:
        quantities.append(
            make_quantity(
                sku_key="operations",
                quantity=float(queue_operations),
                unit="operations/month",
                formula="queue_operations",
                assumption_map=assumption_map,
                input_keys=["queue_operations", "messaging_tier"],
            )
        )
    elif tier == "premium" and queue_operations > 0:
        quantities.append(
            make_quantity(
                sku_key="operations",
                quantity=float(queue_operations),
                unit="operations/month",
                formula="queue_operations",
                assumption_map=assumption_map,
                input_keys=["queue_operations", "messaging_tier"],
                notes=["Premium tier includes high throughput in MU capacity; operations tracked separately."],
            )
        )

    if tier == "standard" and brokered_connections > 0:
        included_connections = min(brokered_connections, _STANDARD_INCLUDED_CONNECTIONS)
        billable_connections = max(0, brokered_connections - _STANDARD_INCLUDED_CONNECTIONS)
        included_usage.append(
            IncludedUsage(
                sku_key="brokered_connections",
                quantity=float(included_connections),
                unit="connections/month",
                description=(
                    f"Standard tier includes {_STANDARD_INCLUDED_CONNECTIONS} brokered connections."
                ),
                source="tier",
            )
        )
        quantities.append(
            make_quantity(
                sku_key="brokered_connections",
                quantity=float(billable_connections),
                unit="connections/month",
                formula=f"max(0, brokered_connections - {_STANDARD_INCLUDED_CONNECTIONS})",
                assumption_map=assumption_map,
                input_keys=["brokered_connections", "messaging_tier"],
                raw_quantity=float(brokered_connections),
                notes=[
                    f"Standard tier includes {_STANDARD_INCLUDED_CONNECTIONS} brokered connections."
                ],
                warnings=(
                    ["brokered_connections exceeds Standard tier included allowance."]
                    if billable_connections > 0
                    else []
                ),
            )
        )
        if brokered_connections > 0 and brokered_connections <= _STANDARD_INCLUDED_CONNECTIONS:
            warnings.append(
                f"brokered_connections within included {_STANDARD_INCLUDED_CONNECTIONS} allowance."
            )

    if data_egress_gb > 0:
        quantities.append(
            make_quantity(
                sku_key="network_egress_gb",
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
        included_usage=included_usage,
        ready=True,
    )
