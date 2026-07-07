"""Azure Container Apps SKU quantity formulas."""

from __future__ import annotations

from app.pricing.azure.sku_quantities._helpers import (
    MONTHLY_SECONDS,
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
)
from app.pricing.schemas import (
    AzureServicePricingModel,
    MissingAssumption,
    SkuQuantity,
    SkuQuantityResult,
    UsageAssumption,
)

_REQUIRED_KEYS = [
    "requests_per_month",
    "avg_request_duration_seconds",
    "cpu",
    "memory_gb",
    "network_egress_gb",
    "min_replicas",
]


def calculate_container_apps_quantities(
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
    requests = numeric_value(assumption_map, "requests_per_month")
    duration = numeric_value(assumption_map, "avg_request_duration_seconds")
    cpu = numeric_value(assumption_map, "cpu")
    memory_gb = numeric_value(assumption_map, "memory_gb")
    network_egress_gb = numeric_value(assumption_map, "network_egress_gb")
    min_replicas = int(numeric_value(assumption_map, "min_replicas"))

    activity_vcpu_seconds = requests * duration * cpu
    activity_memory_gb_seconds = requests * duration * memory_gb

    warnings: list[str] = []
    vcpu_notes: list[str] = []
    memory_notes: list[str] = []

    if min_replicas > 0:
        baseline_vcpu_seconds = min_replicas * cpu * MONTHLY_SECONDS
        baseline_memory_gb_seconds = min_replicas * memory_gb * MONTHLY_SECONDS
        vcpu_seconds = max(activity_vcpu_seconds, baseline_vcpu_seconds)
        memory_gb_seconds = max(activity_memory_gb_seconds, baseline_memory_gb_seconds)
        vcpu_notes.append(
            f"Always-on baseline applied: max(activity, min_replicas * cpu * {MONTHLY_SECONDS})."
        )
        memory_notes.append(
            f"Always-on baseline applied: max(activity, min_replicas * memory_gb * {MONTHLY_SECONDS})."
        )
        if baseline_vcpu_seconds > activity_vcpu_seconds:
            warnings.append(
                "min_replicas baseline exceeds request-driven activity for vcpu_seconds."
            )
        if baseline_memory_gb_seconds > activity_memory_gb_seconds:
            warnings.append(
                "min_replicas baseline exceeds request-driven activity for memory_gb_seconds."
            )
    else:
        vcpu_seconds = activity_vcpu_seconds
        memory_gb_seconds = activity_memory_gb_seconds

    compute_input_keys = [
        "requests_per_month",
        "avg_request_duration_seconds",
        "cpu",
        "memory_gb",
        "min_replicas",
    ]
    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month"],
        ),
        make_quantity(
            sku_key="vcpu_seconds",
            quantity=vcpu_seconds,
            unit="vCPU-seconds/month",
            formula=(
                "max(requests_per_month * avg_request_duration_seconds * cpu, "
                "min_replicas * cpu * monthly_seconds)"
                if min_replicas > 0
                else "requests_per_month * avg_request_duration_seconds * cpu"
            ),
            assumption_map=assumption_map,
            input_keys=compute_input_keys,
            notes=vcpu_notes,
            warnings=warnings,
        ),
        make_quantity(
            sku_key="memory_gb_seconds",
            quantity=memory_gb_seconds,
            unit="GiB-seconds/month",
            formula=(
                "max(requests_per_month * avg_request_duration_seconds * memory_gb, "
                "min_replicas * memory_gb * monthly_seconds)"
                if min_replicas > 0
                else "requests_per_month * avg_request_duration_seconds * memory_gb"
            ),
            assumption_map=assumption_map,
            input_keys=compute_input_keys,
            notes=memory_notes,
            warnings=warnings,
        ),
        make_quantity(
            sku_key="network_egress_gb",
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
