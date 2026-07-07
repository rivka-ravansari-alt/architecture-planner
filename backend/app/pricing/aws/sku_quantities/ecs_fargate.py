"""ECS Fargate SKU quantity formulas."""

from __future__ import annotations

from app.pricing.aws.sku_quantities._helpers import (
    MONTHLY_HOURS,
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
)
from app.pricing.schemas import AwsServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

_REQUIRED_KEYS = [
    "requests_per_month",
    "avg_request_duration_seconds",
    "cpu",
    "memory_gb",
    "network_egress_gb",
    "min_tasks",
]


def calculate_ecs_fargate_quantities(
    model: AwsServicePricingModel,
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
    requests = numeric_value(assumption_map, "requests_per_month")
    duration = numeric_value(assumption_map, "avg_request_duration_seconds")
    cpu = numeric_value(assumption_map, "cpu")
    memory_gb = numeric_value(assumption_map, "memory_gb")
    network_egress_gb = numeric_value(assumption_map, "network_egress_gb")
    min_tasks = int(numeric_value(assumption_map, "min_tasks"))

    activity_vcpu_hours = requests * duration * cpu / 3600
    activity_memory_gb_hours = requests * duration * memory_gb / 3600

    warnings: list[str] = []
    if min_tasks > 0:
        baseline_vcpu_hours = min_tasks * cpu * MONTHLY_HOURS
        baseline_memory_gb_hours = min_tasks * memory_gb * MONTHLY_HOURS
        vcpu_hours = max(activity_vcpu_hours, baseline_vcpu_hours)
        memory_gb_hours = max(activity_memory_gb_hours, baseline_memory_gb_hours)
        if baseline_vcpu_hours > activity_vcpu_hours:
            warnings.append("min_tasks baseline exceeds request-driven activity for vcpu_hours.")
    else:
        vcpu_hours = activity_vcpu_hours
        memory_gb_hours = activity_memory_gb_hours

    compute_input_keys = [
        "requests_per_month",
        "avg_request_duration_seconds",
        "cpu",
        "memory_gb",
        "min_tasks",
    ]
    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="vcpu_hours",
            quantity=vcpu_hours,
            unit="vCPU-hours/month",
            formula="max(requests * duration * cpu / 3600, min_tasks * cpu * hours_per_month)",
            assumption_map=assumption_map,
            input_keys=compute_input_keys,
            warnings=warnings,
        ),
        make_quantity(
            sku_key="memory_gb_hours",
            quantity=memory_gb_hours,
            unit="GiB-hours/month",
            formula="max(requests * duration * memory_gb / 3600, min_tasks * memory_gb * hours_per_month)",
            assumption_map=assumption_map,
            input_keys=compute_input_keys,
            warnings=warnings,
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
