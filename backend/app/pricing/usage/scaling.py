"""Deterministic scaling from per-user behavioral assumptions to billing inputs."""

from __future__ import annotations

from typing import Any

from app.pricing.schemas import AssumptionConfidence, AssumptionSource, UsageAssumption
from app.pricing.usage.behavioral_models import ServiceBehavioralModel, _KB_PER_GB, get_behavioral_model


def scale_behavioral_assumptions(
    service: str,
    *,
    behavioral: dict[str, UsageAssumption],
    config: dict[str, UsageAssumption],
    expected_users: int,
) -> dict[str, UsageAssumption]:
    """Convert per-user behavioral inputs into project-level billing assumptions."""
    model = get_behavioral_model(service)
    if model is None:
        return {**behavioral, **config}

    scaler = _SCALERS.get(service)
    if scaler is None:
        return {**behavioral, **config}

    behavioral_values = _values(behavioral)
    if "static_storage_gb" in config:
        behavioral_values["static_storage_gb"] = config["static_storage_gb"].value

    billing_values = scaler(behavioral_values, expected_users)
    billing: dict[str, UsageAssumption] = {}
    reasoning_context = dict(behavioral)
    if "static_storage_gb" in config:
        reasoning_context["static_storage_gb"] = config["static_storage_gb"]

    for key, value in billing_values.items():
        config_assumption = config.get(key)
        if config_assumption is not None:
            billing[key] = config_assumption
            continue
        billing[key] = UsageAssumption(
            key=key,
            value=value,
            unit=_billing_unit(service, key),
            source=AssumptionSource.inferred,
            confidence=AssumptionConfidence.high,
            reasoning=_scaling_reasoning(
                service,
                key,
                value,
                reasoning_context,
                expected_users,
            ),
        )

    for key, assumption in config.items():
        if key not in billing:
            billing[key] = assumption

    return billing


def _values(assumptions: dict[str, UsageAssumption]) -> dict[str, Any]:
    return {key: item.value for key, item in assumptions.items()}


def _billing_unit(service: str, key: str) -> str | None:
    from app.pricing.aws.registry import get_aws_pricing_model
    from app.pricing.azure.registry import get_azure_pricing_model
    from app.pricing.gcp.registry import get_gcp_pricing_model

    pricing_model = (
        get_aws_pricing_model(service)
        or get_azure_pricing_model(service)
        or get_gcp_pricing_model(service)
    )
    if pricing_model is None:
        return None
    for input_def in pricing_model.pricing_model.required_inputs:
        if input_def.key == key:
            return input_def.unit
    return None


def _scaling_reasoning(
    service: str,
    billing_key: str,
    value: int | float | str | bool,
    behavioral: dict[str, UsageAssumption],
    expected_users: int,
) -> str:
    notes = {
        "requests_per_month": _requests_reasoning(behavioral, expected_users, value),
        "executions_per_month": _executions_reasoning(behavioral, expected_users, value),
        "network_egress_gb": _egress_reasoning(behavioral, expected_users, value),
        "storage_gb": _storage_reasoning(behavioral, expected_users, value),
        "backup_storage_gb": _backup_reasoning(behavioral, expected_users, value),
        "write_operations": _write_ops_reasoning(behavioral, expected_users, value),
        "read_operations": _read_ops_reasoning(behavioral, expected_users, value),
        "data_egress_gb": _blob_egress_reasoning(behavioral, expected_users, value),
        "queue_operations": _queue_ops_reasoning(behavioral, expected_users, value),
        "brokered_connections": _connections_reasoning(behavioral, expected_users, value),
        "data_egress_gb": _blob_egress_reasoning(behavioral, expected_users, value),
    }
    return notes.get(
        billing_key,
        f"Scaled deterministically from per-user behavioral assumptions for {expected_users:,} users.",
    )


def _requests_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    sessions = behavioral.get("sessions_per_user_per_month")
    rps = behavioral.get("requests_per_session")
    if sessions and rps:
        return (
            f"Scaled: {users:,} users × {sessions.value} sessions/user/month "
            f"× {rps.value} requests/session = {total:,} requests/month."
        )
    return f"Scaled to {total:,} requests/month for {users:,} users."


def _executions_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    sessions = behavioral.get("sessions_per_user_per_month")
    inv = behavioral.get("invocations_per_session")
    if sessions and inv:
        return (
            f"Scaled: {users:,} users × {sessions.value} sessions/user/month "
            f"× {inv.value} invocations/session = {total:,} executions/month."
        )
    return f"Scaled to {total:,} executions/month for {users:,} users."


def _egress_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    size = behavioral.get("avg_response_size_kb")
    if size:
        return (
            f"Scaled from per-request egress ({size.value} KB/request) across "
            f"{users:,} users → {total} GB/month."
        )
    return f"Scaled network egress to {total} GB/month for {users:,} users."


def _storage_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    per_user = behavioral.get("storage_gb_per_user")
    static = behavioral.get("static_storage_gb")
    if static and per_user:
        return (
            f"Scaled: {static.value} GB static + {users:,} users × "
            f"{per_user.value} GB/user = {total} GB."
        )
    if per_user:
        return (
            f"Scaled: {users:,} users × {per_user.value} GB/user = {total} GB."
        )
    return f"Scaled storage to {total} GB for {users:,} users."


def _backup_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    per_user = behavioral.get("backup_storage_gb_per_user")
    if per_user:
        return (
            f"Scaled: {users:,} users × {per_user.value} GB/user/month = {total} GB/month."
        )
    return f"Scaled backup storage to {total} GB/month for {users:,} users."


def _write_ops_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    per_user = behavioral.get("writes_per_user_per_month")
    if per_user:
        return (
            f"Scaled: {users:,} users × {per_user.value} writes/user/month "
            f"= {total:,} write operations/month."
        )
    return f"Scaled write operations to {total:,}/month for {users:,} users."


def _read_ops_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    per_user = behavioral.get("reads_per_user_per_month")
    if per_user:
        return (
            f"Scaled: {users:,} users × {per_user.value} reads/user/month "
            f"= {total:,} read operations/month."
        )
    return f"Scaled read operations to {total:,}/month for {users:,} users."


def _blob_egress_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    reads = behavioral.get("reads_per_user_per_month")
    size = behavioral.get("avg_download_size_kb")
    if reads and size:
        return (
            f"Scaled: {users:,} users × {reads.value} reads/user × "
            f"{size.value} KB/read → {total} GB/month egress."
        )
    return f"Scaled blob egress to {total} GB/month for {users:,} users."


def _queue_ops_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    messages = behavioral.get("messages_per_user_per_month")
    if messages:
        return (
            f"Scaled: {users:,} users × {messages.value} messages/user/month "
            f"= {total:,} queue operations/month."
        )
    return f"Scaled queue operations to {total:,}/month for {users:,} users."


def _connections_reasoning(
    behavioral: dict[str, UsageAssumption],
    users: int,
    total: int | float | str | bool,
) -> str:
    per_100 = behavioral.get("concurrent_connections_per_100_users")
    if per_100:
        return (
            f"Scaled: ({users:,} users / 100) × {per_100.value} connections "
            f"= {total:,} brokered connections."
        )
    return f"Scaled brokered connections to {total:,} for {users:,} users."


def _session_requests_per_session(behavioral: dict[str, Any]) -> float:
    if "requests_per_session" in behavioral:
        return float(behavioral["requests_per_session"])
    if "invocations_per_session" in behavioral:
        return float(behavioral["invocations_per_session"])
    raise KeyError("requests_per_session")


def _scale_container_apps(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    sessions = float(behavioral["sessions_per_user_per_month"])
    rps = _session_requests_per_session(behavioral)
    response_kb = float(behavioral["avg_response_size_kb"])
    requests = int(users * sessions * rps)
    egress_gb = round(requests * response_kb / _KB_PER_GB, 2)
    return {
        "requests_per_month": requests,
        "network_egress_gb": egress_gb,
    }


def _scale_functions(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    sessions = float(behavioral["sessions_per_user_per_month"])
    invocations = _session_requests_per_session(behavioral)
    response_kb = float(behavioral["avg_response_size_kb"])
    executions = int(users * sessions * invocations)
    egress_gb = round(executions * response_kb / _KB_PER_GB, 2)
    return {
        "executions_per_month": executions,
        "network_egress_gb": egress_gb,
    }


def _scale_sql(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    storage_per_user = float(behavioral["storage_gb_per_user"])
    backup_per_user = float(
        behavioral.get("backup_storage_gb_per_user", storage_per_user * 0.1)
    )
    return {
        "storage_gb": max(1.0, round(users * storage_per_user, 2)),
        "backup_storage_gb": round(users * backup_per_user, 2),
    }


def _scale_blob(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    storage_per_user = float(behavioral["storage_gb_per_user"])
    writes = float(behavioral["writes_per_user_per_month"])
    reads = float(behavioral["reads_per_user_per_month"])
    download_kb = float(behavioral.get("avg_download_size_kb", 0))
    static_gb = float(behavioral.get("static_storage_gb", 0))
    read_ops = int(users * reads)
    return {
        "storage_gb": round(static_gb + users * storage_per_user, 2),
        "write_operations": int(users * writes),
        "read_operations": read_ops,
        "data_retrieval_gb": 0.0,
        "data_egress_gb": round(read_ops * download_kb / _KB_PER_GB, 2),
    }


def _scale_queue(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    messages = float(behavioral["messages_per_user_per_month"])
    msg_kb = float(behavioral.get("avg_message_size_kb", 1))
    queue_ops = int(users * messages)
    storage_gb = max(0.01, round(queue_ops * msg_kb / _KB_PER_GB, 2))
    egress_gb = round(queue_ops * msg_kb / _KB_PER_GB, 2)
    return {
        "queue_operations": queue_ops,
        "storage_gb": storage_gb,
        "data_egress_gb": egress_gb,
    }


def _scale_service_bus(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    messages = float(behavioral["messages_per_user_per_month"])
    msg_kb = float(behavioral.get("avg_message_size_kb", 1))
    per_100 = float(behavioral.get("concurrent_connections_per_100_users", 10))
    queue_ops = int(users * messages)
    connections = max(10, int((users / 100) * per_100))
    egress_gb = round(queue_ops * msg_kb / _KB_PER_GB, 2)
    return {
        "queue_operations": queue_ops,
        "brokered_connections": connections,
        "data_egress_gb": egress_gb,
    }


def _scale_sqs(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    messages = float(behavioral["messages_per_user_per_month"])
    msg_kb = float(behavioral.get("avg_message_size_kb", 1))
    queue_ops = int(users * messages)
    egress_gb = round(queue_ops * msg_kb / _KB_PER_GB, 2)
    return {
        "queue_operations": queue_ops,
        "data_egress_gb": egress_gb,
    }


def _scale_dynamodb(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    storage_per_user = float(behavioral["storage_gb_per_user"])
    reads = float(behavioral["read_requests_per_user_per_month"])
    writes = float(behavioral["write_requests_per_user_per_month"])
    return {
        "storage_gb": max(1.0, round(users * storage_per_user, 2)),
        "read_requests_per_month": int(users * reads),
        "write_requests_per_month": int(users * writes),
    }


def _scale_api_gateway(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    sessions = float(behavioral["sessions_per_user_per_month"])
    rps = _session_requests_per_session(behavioral)
    response_kb = float(behavioral["avg_response_size_kb"])
    requests = int(users * sessions * rps)
    egress_gb = round(requests * response_kb / _KB_PER_GB, 2)
    return {
        "requests_per_month": requests,
        "data_egress_gb": egress_gb,
    }


def _scale_sns(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    messages = float(behavioral["messages_per_user_per_month"])
    msg_kb = float(behavioral.get("avg_message_size_kb", 1))
    message_count = int(users * messages)
    egress_gb = round(message_count * msg_kb / _KB_PER_GB, 2)
    return {
        "messages_per_month": message_count,
        "data_egress_gb": egress_gb,
    }


def _scale_cloudfront(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    views = float(behavioral["page_views_per_user_per_month"])
    object_kb = float(behavioral["avg_object_size_kb"])
    requests = int(users * views)
    transfer_gb = round(requests * object_kb / _KB_PER_GB, 2)
    return {
        "requests_per_month": requests,
        "data_transfer_gb": transfer_gb,
    }


def _scale_alb(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    requests_per_user = float(behavioral["requests_per_user_per_month"])
    request_kb = float(behavioral["avg_request_size_kb"])
    hours = float(behavioral.get("hours_per_month", 730))
    requests = int(users * requests_per_user)
    egress_gb = round(requests * request_kb / _KB_PER_GB, 2)
    lcu_hours = max(10.0, round(requests / 10_000.0, 2))
    return {
        "hours_per_month": hours,
        "lcu_hours_per_month": lcu_hours,
        "data_egress_gb": egress_gb,
    }


def _scale_secrets_manager(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    api_calls_per_user = float(behavioral["api_calls_per_user_per_month"])
    secrets_count = int(behavioral.get("secrets_count", 1))
    return {
        "secrets_count": max(1, secrets_count),
        "api_calls_per_month": int(users * api_calls_per_user),
    }


def _scale_amplify(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    sessions = float(behavioral["sessions_per_user_per_month"])
    rps = _session_requests_per_session(behavioral)
    requests = int(users * sessions * rps)
    build_minutes = float(behavioral.get("build_minutes_per_month", 0))
    return {
        "hosting_requests_per_month": requests,
        "build_minutes_per_month": build_minutes,
        "data_transfer_gb": round(requests * 0.002, 2),
    }


def _scale_bedrock(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    calls = float(behavioral["ai_calls_per_user_per_month"])
    input_tok = float(behavioral["avg_input_tokens_per_call"])
    output_tok = float(behavioral.get("avg_output_tokens_per_call", 0))
    total_calls = int(users * calls)
    return {
        "input_tokens_per_month": int(total_calls * input_tok),
        "output_tokens_per_month": int(total_calls * output_tok),
    }


def _scale_elasticache(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    return {
        "node_type": behavioral.get("node_type", "cache.t3.micro"),
        "hours_per_month": float(behavioral.get("hours_per_month", 730)),
        "data_egress_gb": round(users * 0.001, 2),
    }


def _scale_opensearch(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    ops = float(behavioral["index_operations_per_user_per_month"])
    queries = float(behavioral["search_queries_per_user_per_month"])
    storage_gb = max(1.0, round(users * ops * 0.001, 2))
    return {
        "instance_hours_per_month": 730.0,
        "storage_gb": storage_gb,
        "data_egress_gb": round(users * queries * 0.0001, 2),
    }


def _scale_athena(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    queries = float(behavioral["analytics_queries_per_user_per_month"])
    tb_per_query = float(behavioral["avg_tb_scanned_per_query"])
    return {"data_scanned_tb_per_month": round(users * queries * tb_per_query, 4)}


def _scale_quicksight(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    return {
        "reader_seats": max(1, int(behavioral.get("reader_seats", 1))),
        "author_seats": max(1, int(behavioral.get("author_seats", 1))),
    }


def _scale_ses(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    emails = float(behavioral["emails_per_user_per_month"])
    count = int(users * emails)
    return {
        "emails_per_month": count,
        "data_egress_gb": round(count * 0.00005, 2),
    }


def _scale_cloudwatch(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    api_calls = float(behavioral["api_calls_per_user_per_month"])
    metrics = int(behavioral.get("custom_metrics_count", max(5, users // 100)))
    return {
        "custom_metrics_count": metrics,
        "api_requests_per_month": int(users * api_calls),
    }


def _scale_cloudwatch_logs(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    events = float(behavioral["log_events_per_user_per_month"])
    event_kb = float(behavioral.get("avg_log_event_kb", 0.5))
    ingestion_gb = round(users * events * event_kb / _KB_PER_GB, 2)
    return {
        "log_ingestion_gb_per_month": max(0.01, ingestion_gb),
        "log_storage_gb": round(ingestion_gb * 0.5, 2),
    }


def _scale_cloudwatch_dashboards(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    dashboards = int(behavioral.get("dashboard_count", 1))
    hours = float(behavioral.get("hours_per_month", 730))
    return {"dashboard_hours_per_month": dashboards * hours}


def _scale_cloudwatch_alarms(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    alarms = int(behavioral.get("standard_alarms_count", max(1, users // 1000)))
    hours = float(behavioral.get("hours_per_month", 730))
    return {
        "standard_alarms_count": alarms,
        "alarm_evaluations_per_month": int(alarms * hours * 60),
    }


def _scale_ssm(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    reads = float(behavioral["config_reads_per_user_per_month"])
    parameters = int(behavioral.get("parameters_count", 10))
    return {
        "parameters_count": max(1, parameters),
        "api_calls_per_month": int(users * reads),
    }


def _scale_appconfig(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    configs = int(behavioral.get("configurations_count", 3))
    events = int(behavioral.get("deployment_events_per_month", 4))
    return {
        "configurations_count": max(1, configs),
        "deployment_events_per_month": max(0, events),
    }


def _scale_xray(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    traces = float(behavioral["traced_requests_per_user_per_month"])
    ingested = int(users * traces)
    return {
        "traces_ingested_per_month": ingested,
        "traces_scanned_per_month": int(ingested * 0.1),
    }


def _scale_web_app_hosting(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    sessions = float(behavioral["sessions_per_user_per_month"])
    rps = float(behavioral["requests_per_session"])
    response_kb = float(behavioral.get("avg_response_size_kb", 2))
    requests = int(users * sessions * rps)
    egress_gb = round(requests * response_kb / _KB_PER_GB, 2)
    return {
        "instance_hours_per_month": float(behavioral.get("instance_hours_per_month", 730)),
        "requests_per_month": requests,
        "data_egress_gb": egress_gb,
        "hosting_requests_per_month": requests,
        "build_minutes_per_month": float(behavioral.get("build_minutes_per_month", 30)),
        "data_transfer_gb": egress_gb,
    }


def _scale_cosmos_db(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    reads = float(behavioral.get("reads_per_user_per_month", 0))
    writes = float(behavioral.get("writes_per_user_per_month", 0))
    storage_kb = float(behavioral.get("storage_kb_per_user", 64))
    request_units = int(users * (reads + writes))
    storage_gb = max(1.0, round(users * storage_kb / 1024, 2))
    return {
        "request_units_per_month": max(100_000, request_units),
        "storage_gb": storage_gb,
        "data_egress_gb": round(storage_gb * 0.1, 2),
        "read_requests_per_month": int(users * reads),
        "write_requests_per_month": int(users * writes),
        "delete_requests_per_month": int(users * writes * 0.1),
    }


def _scale_notification_hubs(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    notif = float(
        behavioral.get("notifications_per_user_per_month")
        or behavioral.get("messages_per_user_per_month", 0)
    )
    msg_kb = float(behavioral.get("avg_message_size_kb", 1))
    count = int(users * notif)
    return {
        "push_notifications_per_month": count,
        "messages_per_month": count,
        "namespace_hours_per_month": float(behavioral.get("namespace_hours_per_month", 730)),
        "data_egress_gb": round(count * msg_kb / _KB_PER_GB, 2),
    }


def _scale_log_analytics(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    events = float(behavioral.get("log_events_per_user_per_month", 0))
    event_kb = float(behavioral.get("avg_log_event_kb", 0.5))
    log_kb = float(behavioral.get("log_kb_per_user_per_month", events * event_kb))
    ingestion_gb = round(users * log_kb / _KB_PER_GB, 2)
    return {
        "log_ingestion_gb_per_month": max(0.01, ingestion_gb),
        "log_retention_gb": round(max(0.01, ingestion_gb) * 0.5, 2),
        "log_storage_gb": round(max(0.01, ingestion_gb) * 0.5, 2),
    }


def _scale_monitoring_config(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    api_calls = float(behavioral.get("api_calls_per_user_per_month", 0))
    return {
        "metrics_count": int(behavioral.get("custom_metrics_count", max(1, users // 100))),
        "alert_rules_count": int(behavioral.get("alert_rules_count", 1)),
        "alert_policies_count": int(behavioral.get("alert_policies_count", 1)),
        "api_requests_per_month": int(users * api_calls),
        "custom_metrics_count": int(behavioral.get("custom_metrics_count", max(1, users // 100))),
    }


def _scale_app_configuration(behavioral: dict[str, Any], users: int) -> dict[str, Any]:
    reads = float(behavioral.get("config_reads_per_user_per_month", 0))
    stores = int(behavioral.get("configuration_stores", 1))
    configs = int(behavioral.get("configurations_count", stores))
    return {
        "configuration_stores": max(1, stores),
        "configurations_count": max(1, configs),
        "requests_per_month": max(0, int(users * reads)),
        "deployment_events_per_month": int(behavioral.get("deployment_events_per_month", 4)),
    }


_SCALERS = {
    "Azure Container Apps": _scale_container_apps,
    "Azure Functions": _scale_functions,
    "Azure SQL Database": _scale_sql,
    "Azure Blob Storage": _scale_blob,
    "Azure Queue Storage": _scale_queue,
    "Azure Service Bus": _scale_service_bus,
    "Azure App Service": _scale_web_app_hosting,
    "API Management": _scale_api_gateway,
    "Azure Cosmos DB": _scale_cosmos_db,
    "Notification Hubs": _scale_notification_hubs,
    "Log Analytics": _scale_log_analytics,
    "Azure Monitor": _scale_monitoring_config,
    "Azure App Configuration": _scale_app_configuration,
    "Application Insights": _scale_log_analytics,
    "Lambda": _scale_functions,
    "ECS Fargate": _scale_container_apps,
    "RDS": _scale_sql,
    "DynamoDB": _scale_dynamodb,
    "S3": _scale_blob,
    "SQS": _scale_sqs,
    "API Gateway": _scale_api_gateway,
    "SNS": _scale_sns,
    "CloudFront": _scale_cloudfront,
    "Application Load Balancer": _scale_alb,
    "Secrets Manager": _scale_secrets_manager,
    "Amplify": _scale_amplify,
    "Amplify Hosting": _scale_amplify,
    "Bedrock": _scale_bedrock,
    "ElastiCache": _scale_elasticache,
    "OpenSearch Service": _scale_opensearch,
    "Athena": _scale_athena,
    "QuickSight": _scale_quicksight,
    "SES": _scale_ses,
    "CloudWatch": _scale_cloudwatch,
    "CloudWatch Logs": _scale_cloudwatch_logs,
    "CloudWatch Dashboards": _scale_cloudwatch_dashboards,
    "CloudWatch Alarms": _scale_cloudwatch_alarms,
    "SSM Parameter Store": _scale_ssm,
    "AppConfig": _scale_appconfig,
    "X-Ray": _scale_xray,
    "Cloud Run": _scale_container_apps,
    "Cloud Run Functions": _scale_functions,
    "Cloud SQL": _scale_sql,
    "Cloud Firestore": _scale_dynamodb,
    "Cloud Storage": _scale_blob,
    "Cloud Pub/Sub": _scale_service_bus,
    "Cloud Tasks": _scale_queue,
    "Cloud Memorystore for Redis": _scale_elasticache,
    "BigQuery": _scale_athena,
    "Cloud Logging": _scale_cloudwatch_logs,
    "Cloud Monitoring": _scale_cloudwatch,
    "Cloud Trace": _scale_xray,
    "Firebase": _scale_amplify,
    "Firebase Hosting": _scale_amplify,
    "Networking": _scale_cloudfront,
    "Gemini API": _scale_bedrock,
    "Vertex AI": _scale_bedrock,
    "Vertex AI Search": _scale_opensearch,
}


def all_behavioral_input_keys(model: ServiceBehavioralModel) -> frozenset[str]:
    return frozenset(item.key for item in model.behavioral_inputs)


def all_llm_input_keys(model: ServiceBehavioralModel) -> frozenset[str]:
    return all_behavioral_input_keys(model) | model.config_input_keys
