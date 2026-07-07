"""Azure Functions SKU quantity formulas."""

from __future__ import annotations

from app.pricing.azure.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    default_numeric,
    make_quantity,
    numeric_value,
    string_value,
)
from app.pricing.schemas import (
    AzureServicePricingModel,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)

_REQUIRED_KEYS = ["executions_per_month"]


def calculate_functions_quantities(
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
    plan = string_value(assumption_map, "plan").strip().casefold()
    executions = numeric_value(assumption_map, "executions_per_month")
    duration_ms = default_numeric(model, assumption_map, "avg_execution_duration_ms")
    memory_mb = default_numeric(model, assumption_map, "memory_mb")
    network_egress_gb = default_numeric(model, assumption_map, "network_egress_gb")

    duration_seconds = duration_ms / 1000
    memory_gb = memory_mb / 1024
    execution_time_gb_seconds = executions * duration_seconds * memory_gb
    vcpu_hours = executions * duration_seconds / 3600

    compute_input_keys = [
        "executions_per_month",
        "avg_execution_duration_ms",
        "memory_mb",
    ]
    quantities: list[SkuQuantity] = []

    if plan == "premium":
        quantities.append(
            make_quantity(
                sku_key="vcpu_hours",
                quantity=vcpu_hours,
                unit="vCPU-hours/month",
                formula=(
                    "executions_per_month * (avg_execution_duration_ms / 1000) / 3600"
                ),
                assumption_map=assumption_map,
                input_keys=["plan", "executions_per_month", "avg_execution_duration_ms"],
                notes=["Premium plan bills vCPU-hours instead of GB-seconds."],
            )
        )
    else:
        quantities.extend(
            [
                make_quantity(
                    sku_key="executions",
                    quantity=float(executions),
                    unit="executions/month",
                    formula="executions_per_month",
                    assumption_map=assumption_map,
                    input_keys=["executions_per_month"],
                ),
                make_quantity(
                    sku_key="execution_time_gb_seconds",
                    quantity=execution_time_gb_seconds,
                    unit="GB-seconds/month",
                    formula=(
                        "executions_per_month * (avg_execution_duration_ms / 1000) "
                        "* (memory_mb / 1024)"
                    ),
                    assumption_map=assumption_map,
                    input_keys=compute_input_keys,
                ),
            ]
        )

    quantities.append(
        make_quantity(
            sku_key="network_egress_gb",
            quantity=float(network_egress_gb),
            unit="GB/month",
            formula="network_egress_gb",
            assumption_map=assumption_map,
            input_keys=["network_egress_gb"],
        )
    )

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
