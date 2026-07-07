"""SKU quantity calculators for extended GCP catalog services."""

from __future__ import annotations

from collections.abc import Callable

from app.pricing.gcp.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import GcpServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

SkuCalculator = Callable[[GcpServicePricingModel, list[UsageAssumption]], SkuQuantityResult]


def _direct_sku(
    *,
    sku_key: str,
    assumption_key: str,
    unit: str,
    assumption_map: dict[str, UsageAssumption],
    input_keys: list[str] | None = None,
) -> SkuQuantity:
    keys = input_keys or [assumption_key]
    quantity = float(numeric_value(assumption_map, assumption_key))
    return make_quantity(
        sku_key=sku_key,
        quantity=quantity,
        unit=unit,
        formula=assumption_key,
        assumption_map=assumption_map,
        input_keys=keys,
    )


def _optional_direct_sku(
    *,
    sku_key: str,
    assumption_key: str,
    unit: str,
    assumption_map: dict[str, UsageAssumption],
    default: int | float = 0,
    input_keys: list[str] | None = None,
) -> SkuQuantity | None:
    value = optional_numeric(assumption_map, assumption_key, default)
    if value <= 0:
        return None
    keys = input_keys or [assumption_key]
    return make_quantity(
        sku_key=sku_key,
        quantity=float(value),
        unit=unit,
        formula=assumption_key,
        assumption_map=assumption_map,
        input_keys=keys,
    )


def _build_result(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
    required_keys: list[str],
    quantities: list[SkuQuantity],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=required_keys)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)


def calculate_firebase_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["hosting_requests_per_month"]
    assumption_map = assumptions_by_key(resolved)
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    hosting = numeric_value(assumption_map, "hosting_requests_per_month")
    messages = optional_numeric(assumption_map, "messages_per_month", 0)
    total_requests = float(hosting) + float(messages)

    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="requests",
            quantity=total_requests,
            unit="requests/month",
            formula="hosting_requests_per_month + messages_per_month",
            assumption_map=assumption_map,
            input_keys=["hosting_requests_per_month", "messages_per_month"],
        ),
    ]
    egress = _optional_direct_sku(
        sku_key="egress_gb",
        assumption_key="data_transfer_gb",
        unit="GB/month",
        assumption_map=assumption_map,
    )
    if egress:
        quantities.append(egress)
    return _build_result(model, resolved, required, quantities)


def calculate_firebase_hosting_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["hosting_requests_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="requests",
            assumption_key="hosting_requests_per_month",
            unit="requests/month",
            assumption_map=assumption_map,
        ),
    ]
    egress = _optional_direct_sku(
        sku_key="egress_gb",
        assumption_key="data_transfer_gb",
        unit="GB/month",
        assumption_map=assumption_map,
    )
    if egress:
        quantities.append(egress)
    return _build_result(model, resolved, required, quantities)


def calculate_bigquery_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["data_scanned_tb_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="data_scanned_tb",
            assumption_key="data_scanned_tb_per_month",
            unit="TB/month",
            assumption_map=assumption_map,
        ),
    ]
    storage = _optional_direct_sku(
        sku_key="storage_gb_month",
        assumption_key="storage_gb",
        unit="GB-months",
        assumption_map=assumption_map,
    )
    if storage:
        quantities.append(storage)
    return _build_result(model, resolved, required, quantities)


def calculate_cloud_logging_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["log_ingestion_gb_per_month"]
    assumption_map = assumptions_by_key(resolved)
    storage = optional_numeric(assumption_map, "log_storage_gb", 0)
    quantities = [
        _direct_sku(
            sku_key="ingestion_gb",
            assumption_key="log_ingestion_gb_per_month",
            unit="GB/month",
            assumption_map=assumption_map,
        ),
        make_quantity(
            sku_key="storage_gb_month",
            quantity=float(storage),
            unit="GB-months",
            formula="log_storage_gb",
            assumption_map=assumption_map,
            input_keys=["log_storage_gb"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_cloud_monitoring_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    assumption_map = assumptions_by_key(resolved)
    metrics = optional_numeric(assumption_map, "custom_metrics_count", 0)
    api_requests = optional_numeric(assumption_map, "api_requests_per_month", 0)
    policies = optional_numeric(assumption_map, "alert_policies_count", 1)
    quantities = [
        make_quantity(
            sku_key="custom_metrics",
            quantity=float(metrics),
            unit="metric-months",
            formula="custom_metrics_count",
            assumption_map=assumption_map,
            input_keys=["custom_metrics_count"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(api_requests),
            unit="requests/month",
            formula="api_requests_per_month",
            assumption_map=assumption_map,
            input_keys=["api_requests_per_month"],
        ),
        make_quantity(
            sku_key="alert_policies",
            quantity=float(policies),
            unit="policy-months",
            formula="alert_policies_count",
            assumption_map=assumption_map,
            input_keys=["alert_policies_count"],
        ),
    ]
    return _build_result(model, resolved, [], quantities)


def calculate_cloud_trace_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["spans_ingested_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="spans_ingested",
            assumption_key="spans_ingested_per_month",
            unit="spans/month",
            assumption_map=assumption_map,
        ),
    ]
    scanned = _optional_direct_sku(
        sku_key="spans_scanned",
        assumption_key="spans_scanned_per_month",
        unit="spans/month",
        assumption_map=assumption_map,
    )
    if scanned:
        quantities.append(scanned)
    return _build_result(model, resolved, required, quantities)


def calculate_gemini_api_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["input_tokens_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="input_tokens",
            assumption_key="input_tokens_per_month",
            unit="tokens/month",
            assumption_map=assumption_map,
        ),
    ]
    output = _optional_direct_sku(
        sku_key="output_tokens",
        assumption_key="output_tokens_per_month",
        unit="tokens/month",
        assumption_map=assumption_map,
    )
    if output:
        quantities.append(output)
    return _build_result(model, resolved, required, quantities)


def calculate_vertex_ai_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["input_tokens_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="input_tokens",
            assumption_key="input_tokens_per_month",
            unit="tokens/month",
            assumption_map=assumption_map,
        ),
    ]
    output = _optional_direct_sku(
        sku_key="output_tokens",
        assumption_key="output_tokens_per_month",
        unit="tokens/month",
        assumption_map=assumption_map,
    )
    if output:
        quantities.append(output)
    hours = _optional_direct_sku(
        sku_key="prediction_hours",
        assumption_key="prediction_hours_per_month",
        unit="hours/month",
        assumption_map=assumption_map,
    )
    if hours:
        quantities.append(hours)
    return _build_result(model, resolved, required, quantities)


def calculate_vertex_ai_search_quantities(
    model: GcpServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["search_queries_per_month", "storage_gb"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="requests",
            assumption_key="search_queries_per_month",
            unit="queries/month",
            assumption_map=assumption_map,
        ),
        _direct_sku(
            sku_key="storage_gb_month",
            assumption_key="storage_gb",
            unit="GB-months",
            assumption_map=assumption_map,
        ),
    ]
    egress = _optional_direct_sku(
        sku_key="egress_gb",
        assumption_key="data_egress_gb",
        unit="GB/month",
        assumption_map=assumption_map,
    )
    if egress:
        quantities.append(egress)
    return _build_result(model, resolved, required, quantities)


EXTENDED_GCP_SKU_CALCULATORS: dict[str, SkuCalculator] = {
    "Firebase": calculate_firebase_quantities,
    "Firebase Hosting": calculate_firebase_hosting_quantities,
    "BigQuery": calculate_bigquery_quantities,
    "Cloud Logging": calculate_cloud_logging_quantities,
    "Cloud Monitoring": calculate_cloud_monitoring_quantities,
    "Cloud Trace": calculate_cloud_trace_quantities,
    "Gemini API": calculate_gemini_api_quantities,
    "Vertex AI": calculate_vertex_ai_quantities,
    "Vertex AI Search": calculate_vertex_ai_search_quantities,
}
