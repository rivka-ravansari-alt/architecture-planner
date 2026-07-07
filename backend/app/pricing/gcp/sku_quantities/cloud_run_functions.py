"""Cloud Run Functions SKU quantity formulas."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    default_numeric,
    make_quantity,
    numeric_value,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = ["executions_per_month"]


def calculate_cloud_run_functions_quantities(
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
    executions = numeric_value(assumption_map, "executions_per_month")
    duration_ms = default_numeric(model, assumption_map, "avg_execution_duration_ms")
    memory_mb = default_numeric(model, assumption_map, "memory_mb")
    network_egress_gb = default_numeric(model, assumption_map, "network_egress_gb")

    duration_seconds = duration_ms / 1000
    memory_gb = memory_mb / 1024
    gb_seconds = executions * duration_seconds * memory_gb

    compute_input_keys = [
        "executions_per_month",
        "avg_execution_duration_ms",
        "memory_mb",
    ]
    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="requests",
            quantity=float(executions),
            unit="executions/month",
            formula="executions_per_month",
            assumption_map=assumption_map,
            input_keys=["executions_per_month"],
        ),
        make_quantity(
            sku_key="gb_seconds",
            quantity=gb_seconds,
            unit="GB-seconds/month",
            formula=(
                "executions_per_month * (avg_execution_duration_ms / 1000) * (memory_mb / 1024)"
            ),
            assumption_map=assumption_map,
            input_keys=compute_input_keys,
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(network_egress_gb),
            unit="GB/month",
            formula="network_egress_gb",
            assumption_map=assumption_map,
            input_keys=["network_egress_gb"],
        ),
    ]

    return SkuQuantityResult(
        service=model.service,
        quantities=quantities,
        missing=[],
        ready=True,
    )
