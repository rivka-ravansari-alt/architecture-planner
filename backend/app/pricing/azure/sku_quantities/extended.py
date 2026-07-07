"""SKU quantity calculators for extended Azure catalog services."""

from __future__ import annotations

from collections.abc import Callable

from app.pricing.azure.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import AzureServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

SkuCalculator = Callable[[AzureServicePricingModel, list[UsageAssumption]], SkuQuantityResult]


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
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
    required_keys: list[str],
    quantities: list[SkuQuantity],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=required_keys)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)


def calculate_app_service_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    hours = optional_numeric(assumption_map, "instance_hours_per_month", 730)
    requests = optional_numeric(assumption_map, "requests_per_month", 0)
    egress = optional_numeric(assumption_map, "data_egress_gb", 0)
    quantities = [
        make_quantity(
            sku_key="instance_hours",
            quantity=float(hours),
            unit="hours/month",
            formula="instance_hours_per_month",
            assumption_map=assumption_map,
            input_keys=["instance_hours_per_month"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(egress),
            unit="GB/month",
            formula="data_egress_gb",
            assumption_map=assumption_map,
            input_keys=["data_egress_gb"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_app_center_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    quantities: list[SkuQuantity] = []
    build = _optional_direct_sku(
        sku_key="build_minutes",
        assumption_key="build_minutes_per_month",
        unit="minutes/month",
        assumption_map=assumption_map,
    )
    if build:
        quantities.append(build)
    test = _optional_direct_sku(
        sku_key="test_minutes",
        assumption_key="test_device_minutes_per_month",
        unit="minutes/month",
        assumption_map=assumption_map,
    )
    if test:
        quantities.append(test)
    if not quantities:
        quantities.append(
            make_quantity(
                sku_key="build_minutes",
                quantity=0.0,
                unit="minutes/month",
                formula="build_minutes_per_month",
                assumption_map=assumption_map,
                input_keys=["build_minutes_per_month"],
            )
        )
    return _build_result(model, resolved, required, quantities)


def calculate_cosmos_db_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["request_units_per_month", "storage_gb"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="request_units",
            assumption_key="request_units_per_month",
            unit="RU/month",
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


def calculate_redis_cache_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["hours_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="instance_hours",
            assumption_key="hours_per_month",
            unit="hours/month",
            assumption_map=assumption_map,
            input_keys=["hours_per_month", "cache_size"],
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


def calculate_cognitive_search_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["storage_gb"]
    assumption_map = assumptions_by_key(resolved)
    su_hours = optional_numeric(assumption_map, "search_units_hours", 730)
    quantities = [
        make_quantity(
            sku_key="search_unit_hours",
            quantity=float(su_hours),
            unit="SU-hours/month",
            formula="search_units_hours",
            assumption_map=assumption_map,
            input_keys=["search_units_hours"],
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


def calculate_foundry_models_quantities(
    model: AzureServicePricingModel,
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


def calculate_notification_hubs_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["push_notifications_per_month"]
    assumption_map = assumptions_by_key(resolved)
    hours = optional_numeric(assumption_map, "namespace_hours_per_month", 730)
    quantities = [
        _direct_sku(
            sku_key="notifications",
            assumption_key="push_notifications_per_month",
            unit="notifications/month",
            assumption_map=assumption_map,
        ),
        make_quantity(
            sku_key="namespace_hours",
            quantity=float(hours),
            unit="hours/month",
            formula="namespace_hours_per_month",
            assumption_map=assumption_map,
            input_keys=["namespace_hours_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_voice_core_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["voice_minutes_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="voice_minutes",
            assumption_key="voice_minutes_per_month",
            unit="minutes/month",
            assumption_map=assumption_map,
        ),
    ]
    sms = _optional_direct_sku(
        sku_key="sms_messages",
        assumption_key="sms_messages_per_month",
        unit="messages/month",
        assumption_map=assumption_map,
    )
    if sms:
        quantities.append(sms)
    return _build_result(model, resolved, required, quantities)


def calculate_application_insights_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["telemetry_gb_per_month"]
    assumption_map = assumptions_by_key(resolved)
    queries = optional_numeric(assumption_map, "log_queries_per_month", 0)
    quantities = [
        _direct_sku(
            sku_key="ingestion_gb",
            assumption_key="telemetry_gb_per_month",
            unit="GB/month",
            assumption_map=assumption_map,
        ),
        make_quantity(
            sku_key="queries",
            quantity=float(queries),
            unit="queries/month",
            formula="log_queries_per_month",
            assumption_map=assumption_map,
            input_keys=["log_queries_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_azure_monitor_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    metrics = optional_numeric(assumption_map, "metrics_count", 0)
    rules = optional_numeric(assumption_map, "alert_rules_count", 1)
    api_requests = optional_numeric(assumption_map, "api_requests_per_month", 0)
    quantities = [
        make_quantity(
            sku_key="custom_metrics",
            quantity=float(metrics),
            unit="metric-months",
            formula="metrics_count",
            assumption_map=assumption_map,
            input_keys=["metrics_count"],
        ),
        make_quantity(
            sku_key="alert_rules",
            quantity=float(rules),
            unit="rule-months",
            formula="alert_rules_count",
            assumption_map=assumption_map,
            input_keys=["alert_rules_count"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(api_requests),
            unit="requests/month",
            formula="api_requests_per_month",
            assumption_map=assumption_map,
            input_keys=["api_requests_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_log_analytics_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["log_ingestion_gb_per_month"]
    assumption_map = assumptions_by_key(resolved)
    retention = optional_numeric(assumption_map, "log_retention_gb", 0)
    quantities = [
        _direct_sku(
            sku_key="ingestion_gb",
            assumption_key="log_ingestion_gb_per_month",
            unit="GB/month",
            assumption_map=assumption_map,
        ),
        make_quantity(
            sku_key="storage_gb_month",
            quantity=float(retention),
            unit="GB-months",
            formula="log_retention_gb",
            assumption_map=assumption_map,
            input_keys=["log_retention_gb"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_power_bi_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    seats = optional_numeric(assumption_map, "pro_seats", 1)
    premium = optional_numeric(assumption_map, "premium_capacity_hours", 0)
    quantities = [
        make_quantity(
            sku_key="pro_seats",
            quantity=float(seats),
            unit="seat-months",
            formula="pro_seats",
            assumption_map=assumption_map,
            input_keys=["pro_seats"],
        ),
        make_quantity(
            sku_key="premium_hours",
            quantity=float(premium),
            unit="hours/month",
            formula="premium_capacity_hours",
            assumption_map=assumption_map,
            input_keys=["premium_capacity_hours"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_key_vault_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    secrets = optional_numeric(assumption_map, "secrets_count", 1)
    operations = optional_numeric(assumption_map, "operations_per_month", 0)
    quantities = [
        make_quantity(
            sku_key="secret_months",
            quantity=float(secrets),
            unit="secret-months",
            formula="secrets_count",
            assumption_map=assumption_map,
            input_keys=["secrets_count"],
        ),
        make_quantity(
            sku_key="operations",
            quantity=float(operations),
            unit="operations/month",
            formula="operations_per_month",
            assumption_map=assumption_map,
            input_keys=["operations_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_app_configuration_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    stores = optional_numeric(assumption_map, "configuration_stores", 1)
    requests = optional_numeric(assumption_map, "requests_per_month", 0)
    quantities = [
        make_quantity(
            sku_key="store_months",
            quantity=float(stores),
            unit="store-months",
            formula="configuration_stores",
            assumption_map=assumption_map,
            input_keys=["configuration_stores"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


EXTENDED_AZURE_SKU_CALCULATORS: dict[str, SkuCalculator] = {
    "Azure App Service": calculate_app_service_quantities,
    "Azure App Center": calculate_app_center_quantities,
    "Azure Cosmos DB": calculate_cosmos_db_quantities,
    "Azure Redis Cache": calculate_redis_cache_quantities,
    "Azure Cognitive Search": calculate_cognitive_search_quantities,
    "Azure Foundry Models": calculate_foundry_models_quantities,
    "Notification Hubs": calculate_notification_hubs_quantities,
    "Azure Voice Core": calculate_voice_core_quantities,
    "Application Insights": calculate_application_insights_quantities,
    "Azure Monitor": calculate_azure_monitor_quantities,
    "Log Analytics": calculate_log_analytics_quantities,
    "Power BI": calculate_power_bi_quantities,
    "Azure Key Vault": calculate_key_vault_quantities,
    "Azure App Configuration": calculate_app_configuration_quantities,
}
