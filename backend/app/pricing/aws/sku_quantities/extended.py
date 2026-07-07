"""SKU quantity calculators for extended AWS catalog services."""

from __future__ import annotations

from collections.abc import Callable

from app.pricing.aws.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import AwsServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption

SkuCalculator = Callable[[AwsServicePricingModel, list[UsageAssumption]], SkuQuantityResult]


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
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
    required_keys: list[str],
    quantities: list[SkuQuantity],
) -> SkuQuantityResult:
    missing = collect_missing_required(model, resolved, keys=required_keys)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)


def calculate_amplify_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["hosting_requests_per_month"]
    assumption_map = assumptions_by_key(resolved)
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
    quantities: list[SkuQuantity] = [
        _direct_sku(
            sku_key="requests",
            assumption_key="hosting_requests_per_month",
            unit="requests/month",
            assumption_map=assumption_map,
        ),
    ]
    build = _optional_direct_sku(
        sku_key="build_minutes",
        assumption_key="build_minutes_per_month",
        unit="minutes/month",
        assumption_map=assumption_map,
    )
    if build:
        quantities.append(build)
    egress = _optional_direct_sku(
        sku_key="egress_gb",
        assumption_key="data_transfer_gb",
        unit="GB/month",
        assumption_map=assumption_map,
    )
    if egress:
        quantities.append(egress)
    return _build_result(model, resolved, required, quantities)


def calculate_amplify_hosting_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    return calculate_amplify_quantities(model, resolved)


def calculate_bedrock_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["input_tokens_per_month"]
    assumption_map = assumptions_by_key(resolved)
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
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


def calculate_elasticache_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["hours_per_month"]
    assumption_map = assumptions_by_key(resolved)
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
    quantities = [
        _direct_sku(
            sku_key="instance_hours",
            assumption_key="hours_per_month",
            unit="hours/month",
            assumption_map=assumption_map,
            input_keys=["hours_per_month", "node_type"],
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


def calculate_opensearch_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["instance_hours_per_month", "storage_gb"]
    assumption_map = assumptions_by_key(resolved)
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)
    quantities = [
        _direct_sku(
            sku_key="instance_hours",
            assumption_key="instance_hours_per_month",
            unit="hours/month",
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


def calculate_athena_quantities(
    model: AwsServicePricingModel,
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
    return _build_result(model, resolved, required, quantities)


def calculate_quicksight_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    reader = optional_numeric(assumption_map, "reader_seats", 1)
    author = optional_numeric(assumption_map, "author_seats", 1)
    quantities = [
        make_quantity(
            sku_key="reader_seats",
            quantity=float(reader),
            unit="seat-months",
            formula="reader_seats",
            assumption_map=assumption_map,
            input_keys=["reader_seats"],
        ),
        make_quantity(
            sku_key="author_seats",
            quantity=float(author),
            unit="seat-months",
            formula="author_seats",
            assumption_map=assumption_map,
            input_keys=["author_seats"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_ses_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["emails_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="requests",
            assumption_key="emails_per_month",
            unit="emails/month",
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


def calculate_cloudwatch_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    metrics = optional_numeric(assumption_map, "custom_metrics_count", 0)
    api_requests = optional_numeric(assumption_map, "api_requests_per_month", 0)
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
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_cloudwatch_logs_quantities(
    model: AwsServicePricingModel,
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


def calculate_cloudwatch_dashboards_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    hours = optional_numeric(assumption_map, "dashboard_hours_per_month", 730)
    quantities = [
        make_quantity(
            sku_key="dashboard_hours",
            quantity=float(hours),
            unit="dashboard-hours/month",
            formula="dashboard_hours_per_month",
            assumption_map=assumption_map,
            input_keys=["dashboard_hours_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_cloudwatch_alarms_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    alarms = optional_numeric(assumption_map, "standard_alarms_count", 1)
    evaluations = optional_numeric(assumption_map, "alarm_evaluations_per_month", 0)
    quantities = [
        make_quantity(
            sku_key="alarms",
            quantity=float(alarms),
            unit="alarm-months",
            formula="standard_alarms_count",
            assumption_map=assumption_map,
            input_keys=["standard_alarms_count"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(evaluations),
            unit="evaluations/month",
            formula="alarm_evaluations_per_month",
            assumption_map=assumption_map,
            input_keys=["alarm_evaluations_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_ssm_parameter_store_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    parameters = optional_numeric(assumption_map, "parameters_count", 1)
    api_calls = optional_numeric(assumption_map, "api_calls_per_month", 0)
    quantities = [
        make_quantity(
            sku_key="parameter_months",
            quantity=float(parameters),
            unit="parameter-months",
            formula="parameters_count",
            assumption_map=assumption_map,
            input_keys=["parameters_count"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(api_calls),
            unit="operations/month",
            formula="api_calls_per_month",
            assumption_map=assumption_map,
            input_keys=["api_calls_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_appconfig_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    configs = optional_numeric(assumption_map, "configurations_count", 1)
    events = optional_numeric(assumption_map, "deployment_events_per_month", 0)
    quantities = [
        make_quantity(
            sku_key="configuration_months",
            quantity=float(configs),
            unit="configuration-months",
            formula="configurations_count",
            assumption_map=assumption_map,
            input_keys=["configurations_count"],
        ),
        make_quantity(
            sku_key="requests",
            quantity=float(events),
            unit="events/month",
            formula="deployment_events_per_month",
            assumption_map=assumption_map,
            input_keys=["deployment_events_per_month"],
        ),
    ]
    return _build_result(model, resolved, required, quantities)


def calculate_xray_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["traces_ingested_per_month"]
    assumption_map = assumptions_by_key(resolved)
    quantities = [
        _direct_sku(
            sku_key="traces_ingested",
            assumption_key="traces_ingested_per_month",
            unit="traces/month",
            assumption_map=assumption_map,
        ),
    ]
    scanned = _optional_direct_sku(
        sku_key="traces_scanned",
        assumption_key="traces_scanned_per_month",
        unit="traces/month",
        assumption_map=assumption_map,
    )
    if scanned:
        quantities.append(scanned)
    return _build_result(model, resolved, required, quantities)


EXTENDED_AWS_SKU_CALCULATORS: dict[str, SkuCalculator] = {
    "Amplify": calculate_amplify_quantities,
    "Amplify Hosting": calculate_amplify_hosting_quantities,
    "Bedrock": calculate_bedrock_quantities,
    "ElastiCache": calculate_elasticache_quantities,
    "OpenSearch Service": calculate_opensearch_quantities,
    "Athena": calculate_athena_quantities,
    "QuickSight": calculate_quicksight_quantities,
    "SES": calculate_ses_quantities,
    "CloudWatch": calculate_cloudwatch_quantities,
    "CloudWatch Logs": calculate_cloudwatch_logs_quantities,
    "CloudWatch Dashboards": calculate_cloudwatch_dashboards_quantities,
    "CloudWatch Alarms": calculate_cloudwatch_alarms_quantities,
    "SSM Parameter Store": calculate_ssm_parameter_store_quantities,
    "AppConfig": calculate_appconfig_quantities,
    "X-Ray": calculate_xray_quantities,
}
