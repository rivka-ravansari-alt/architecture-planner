"""Verification output for Azure SKU quantity formulas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pricing import (
    calculate_azure_sku_quantities,
    calculate_project_azure_sku_quantities,
    ComponentPricingInput,
    apply_project_free_tier,
    FreeTierPoolState,
    get_azure_pricing_model,
    resolve_usage_assumptions,
)
from app.pricing.azure.sku_quantities._helpers import MONTHLY_SECONDS


def qty(result, key: str):
    return next(item for item in result.quantities if item.sku_key == key)


def print_quantity(label: str, q) -> None:
    print(f"\n{label}")
    print(f"  sku_key: {q.sku_key}")
    print(f"  raw_quantity: {q.raw_quantity:,.4f}".rstrip("0").rstrip(".") if q.raw_quantity is not None else "  raw_quantity: (none)")
    print(f"  quantity: {q.quantity:,.4f}".rstrip("0").rstrip("."))
    print(f"  free_tier_deducted: {q.free_tier_deducted:,.4f}".rstrip("0").rstrip("."))
    print(f"  free_tier_applied: {q.free_tier_applied}")
    print(f"  unit: {q.unit}")
    print(f"  formula: {q.formula}")
    print(f"  input_values_used: {json.dumps(q.input_values_used, indent=4)}")
    if q.notes:
        print(f"  notes: {q.notes}")
    if q.warnings:
        print(f"  warnings: {q.warnings}")


def print_adjusted_case(title: str, model, user_provided: dict, sku_keys: tuple[str, ...]) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)

    resolution = resolve_usage_assumptions(model, user_provided=user_provided)
    raw = calculate_azure_sku_quantities(model, resolution.resolved)
    pool = FreeTierPoolState()
    adjusted = apply_project_free_tier(model, raw, pool, resolved=resolution.resolved)

    print("\n  RAW (before free-tier deduction):")
    for key in sku_keys:
        print_quantity(key, qty(raw, key))

    print("\n  ADJUSTED (after free-tier deduction):")
    for key in sku_keys:
        print_quantity(key, qty(adjusted, key))

    if adjusted.included_usage:
        print("\n  included_usage metadata:")
        for item in adjusted.included_usage:
            print(f"    - sku_key: {item.sku_key}, quantity: {item.quantity}, source: {item.source}")
            print(f"      description: {item.description}")

    if adjusted.warnings:
        print("\n  free-tier warnings:")
        for warning in adjusted.warnings:
            print(f"    - {warning}")


def main() -> None:
    model = get_azure_pricing_model("Azure Container Apps")
    assert model is not None

    base = {
        "requests_per_month": 6_000_000,
        "avg_request_duration_seconds": 0.3,
        "cpu": 0.5,
        "memory_gb": 1,
        "network_egress_gb": 50,
    }

    print("=" * 72)
    print("CASE 1: Azure Container Apps — min_replicas = 0")
    print("=" * 72)

    resolution = resolve_usage_assumptions(model, user_provided={**base, "min_replicas": 0})
    result = calculate_azure_sku_quantities(model, resolution.resolved)

    for key in ("requests", "vcpu_seconds", "memory_gb_seconds", "network_egress_gb"):
        print_quantity(key, qty(result, key))

    activity_vcpu = 6_000_000 * 0.3 * 0.5
    activity_mem = 6_000_000 * 0.3 * 1.0
    print("\nManual check (activity-only):")
    print(f"  activity_vcpu_seconds = 6,000,000 × 0.3 × 0.5 = {activity_vcpu:,.0f}")
    print(f"  activity_memory_gb_seconds = 6,000,000 × 0.3 × 1 = {activity_mem:,.0f}")

    print("\n" + "=" * 72)
    print("CASE 2: Azure Container Apps — min_replicas = 1")
    print("=" * 72)

    resolution = resolve_usage_assumptions(model, user_provided={**base, "min_replicas": 1})
    result = calculate_azure_sku_quantities(model, resolution.resolved)

    baseline_vcpu = 1 * 0.5 * MONTHLY_SECONDS
    baseline_mem = 1 * 1.0 * MONTHLY_SECONDS
    final_vcpu = max(activity_vcpu, baseline_vcpu)
    final_mem = max(activity_mem, baseline_mem)

    print(f"\n  activity_vcpu_seconds:        {activity_vcpu:,.0f}")
    print(f"  baseline_vcpu_seconds:        {baseline_vcpu:,.0f}  (= 1 × 0.5 × {MONTHLY_SECONDS:,})")
    print(f"  final_vcpu_seconds:           {final_vcpu:,.0f}")
    print(f"\n  activity_memory_gb_seconds:   {activity_mem:,.0f}")
    print(f"  baseline_memory_gb_seconds:   {baseline_mem:,.0f}  (= 1 × 1 × {MONTHLY_SECONDS:,})")
    print(f"  final_memory_gb_seconds:        {final_mem:,.0f}")

    print_quantity("final vcpu_seconds SKU", qty(result, "vcpu_seconds"))
    print_quantity("final memory_gb_seconds SKU", qty(result, "memory_gb_seconds"))

    print("\n" + "=" * 72)
    print("CASE 3: Azure SQL Database — Standard S1, storage_gb = 300")
    print("=" * 72)

    sql_model = get_azure_pricing_model("Azure SQL Database")
    assert sql_model is not None
    sql_resolution = resolve_usage_assumptions(
        sql_model,
        user_provided={"tier": "Standard S1", "storage_gb": 300},
    )
    sql_result = calculate_azure_sku_quantities(sql_model, sql_resolution.resolved)

    raw_storage = 300
    included = 250
    billable = max(0, raw_storage - included)

    print(f"\n  database_instance_months: {qty(sql_result, 'database_instance_months').quantity:,.0f}")
    print(f"  raw_storage_gb_month: {raw_storage}")
    print(f"  included_storage_gb: {included}")
    print(
        "  billable_storage_before_pricing_model_deduction: "
        f"{billable}  (same as storage_gb_month SKU today; no separate deduction layer yet)"
    )
    print_quantity("storage_gb_month SKU", qty(sql_result, "storage_gb_month"))
    print("\n  included_usage metadata:")
    for item in sql_result.included_usage:
        print(f"    - sku_key: {item.sku_key}")
        print(f"      quantity: {item.quantity}")
        print(f"      unit: {item.unit}")
        print(f"      source: {item.source}")
        print(f"      description: {item.description}")

    print_adjusted_case(
        "CASE 4: Azure Container Apps — free-tier deduction (min_replicas=0)",
        model,
        {**base, "min_replicas": 0},
        ("requests", "vcpu_seconds", "memory_gb_seconds"),
    )

    blob_model = get_azure_pricing_model("Azure Blob Storage")
    assert blob_model is not None
    print_adjusted_case(
        "CASE 5: Azure Blob Storage — Hot LRS 120 GB (5 GB free tier)",
        blob_model,
        {"storage_gb": 120, "access_tier": "Hot", "redundancy": "LRS"},
        ("storage_gb_month",),
    )

    sb_model = get_azure_pricing_model("Azure Service Bus")
    assert sb_model is not None
    print_adjusted_case(
        "CASE 6: Azure Service Bus Standard — 20M operations (13M free tier)",
        sb_model,
        {"messaging_tier": "Standard", "queue_operations": 20_000_000},
        ("operations",),
    )

    print("\n" + "=" * 72)
    print("CASE 7: Project pool — two Container Apps share 2M requests grant")
    print("=" * 72)

    def container_component(component_id: str, order: int, requests: int) -> ComponentPricingInput:
        resolution = resolve_usage_assumptions(
            model,
            user_provided={**base, "min_replicas": 0, "requests_per_month": requests},
        )
        return ComponentPricingInput(
            component_id=component_id,
            order=order,
            azure_service="Azure Container Apps",
            resolved=resolution.resolved,
        )

    project = calculate_project_azure_sku_quantities(
        [
            container_component("worker-a", 0, 1_500_000),
            container_component("worker-b", 1, 1_000_000),
        ]
    )
    for component in project.components:
        req = qty(component, "requests")
        print(f"\n  {component.component_id}:")
        print(f"    raw requests: {req.raw_quantity:,.0f}")
        print(f"    free_tier_deducted: {req.free_tier_deducted:,.0f}")
        print(f"    billable requests: {req.quantity:,.0f}")
    print(f"\n  pool_summary: {json.dumps(project.pool_summary, indent=2)}")

    print("\n" + "=" * 72)
    print("CASE 8: Catalog cost lines (in-memory test catalog)")
    print("=" * 72)

    from app.pricing.catalog_factory import build_azure_cost_calculator

    cost_calculator = build_azure_cost_calculator()
    blob_model = get_azure_pricing_model("Azure Blob Storage")
    assert blob_model is not None
    blob_resolution = resolve_usage_assumptions(
        blob_model,
        user_provided={"storage_gb": 120, "access_tier": "Hot", "redundancy": "LRS"},
    )
    blob_raw = calculate_azure_sku_quantities(blob_model, blob_resolution.resolved)
    blob_pool = FreeTierPoolState()
    blob_adjusted = apply_project_free_tier(
        blob_model,
        blob_raw,
        blob_pool,
        resolved=blob_resolution.resolved,
    )
    from app.pricing.schemas import ComponentSkuResult

    blob_component = ComponentSkuResult(
        component_id="blob-demo",
        service=blob_adjusted.service,
        quantities=blob_adjusted.quantities,
        included_usage=blob_adjusted.included_usage,
        missing=blob_adjusted.missing,
        ready=blob_adjusted.ready,
        warnings=blob_adjusted.warnings,
    )
    blob_cost = cost_calculator.calculate_component(blob_model, blob_component)
    print(f"\n  component subtotal_usd: ${blob_cost.subtotal_usd:,.4f}")
    for line in blob_cost.line_items:
        print(
            f"    - {line.sku_key} ({line.catalog_role}): "
            f"{line.quantity:,.0f} {line.unit} -> "
            f"{line.billable_units:,.4f} x ${line.unit_price_usd} = ${line.monthly_cost_usd:,.4f}"
        )

    print("\n" + "=" * 72)
    print("MISSING INPUT: Azure Container Apps without cpu")
    print("=" * 72)
    print(
        "\nNote: SKU calculation uses only the resolved assumption list passed in."
        "\nIf resolve_usage_assumptions() is called first, model defaults (e.g. cpu=0.5)"
        "\nmay be applied there — that is a separate layer."
    )

    from app.pricing.schemas import AssumptionConfidence, AssumptionSource, UsageAssumption

    resolved_without_cpu = [
        UsageAssumption(
            key="requests_per_month",
            value=6_000_000,
            unit="requests/month",
            source=AssumptionSource.user_provided,
            confidence=AssumptionConfidence.high,
        ),
        UsageAssumption(
            key="avg_request_duration_seconds",
            value=0.3,
            unit="seconds",
            source=AssumptionSource.user_provided,
            confidence=AssumptionConfidence.high,
        ),
        UsageAssumption(
            key="memory_gb",
            value=1,
            unit="GiB",
            source=AssumptionSource.user_provided,
            confidence=AssumptionConfidence.high,
        ),
        UsageAssumption(
            key="network_egress_gb",
            value=50,
            unit="GB/month",
            source=AssumptionSource.user_provided,
            confidence=AssumptionConfidence.high,
        ),
        UsageAssumption(
            key="min_replicas",
            value=0,
            unit="replicas",
            source=AssumptionSource.user_provided,
            confidence=AssumptionConfidence.high,
        ),
    ]

    missing_result = calculate_azure_sku_quantities(model, resolved_without_cpu)
    print("\nAfter calculate_azure_sku_quantities (resolved list without cpu):")
    print(f"  ready: {missing_result.ready}")
    print(f"  quantities count: {len(missing_result.quantities)}")
    print("  missing:")
    for item in missing_result.missing:
        print(f"    - key: {item.key}")
        print(f"      description: {item.description}")
        print(f"      reason: {item.reason}")


if __name__ == "__main__":
    main()
