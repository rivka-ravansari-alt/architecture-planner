"""Build concise, component-specific pricing calculation summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class _SummaryField:
    label: str
    keys: tuple[str, ...]
    format_value: Callable[[Any], str]


def _as_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _format_number(value: Any) -> str:
    number = _as_number(value)
    if number is None:
        return str(value)
    if isinstance(number, int):
        return f"{number:,}"
    text = f"{number:,.4f}".rstrip("0").rstrip(".")
    return text


def _format_with_suffix(suffix: str) -> Callable[[Any], str]:
    return lambda value: f"{_format_number(value)}{suffix}"


def _format_plain(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _format_number(value)


def _lookup(locals_snapshot: dict[str, Any], keys: tuple[str, ...]) -> Any | None:
    for key in keys:
        if "." in key:
            root, attr = key.split(".", 1)
            obj = locals_snapshot.get(root)
            if isinstance(obj, dict) and attr in obj:
                value = obj.get(attr)
                if value is not None and value != "":
                    return value
            continue
        if key in locals_snapshot and locals_snapshot[key] is not None:
            value = locals_snapshot[key]
            if value != "":
                return value
    return None


def _field(label: str, *keys: str, suffix: str = "") -> _SummaryField:
    formatter = _format_with_suffix(suffix) if suffix else _format_plain
    return _SummaryField(label=label, keys=keys, format_value=formatter)


_SERVICE_SUMMARY_FIELDS: dict[str, tuple[_SummaryField, ...]] = {
    "aws_lambda": (
        _field("Requests", "monthly_requests", suffix="/month"),
        _field("Memory", "memory_mb", suffix=" MB"),
        _field("Execution", "average_execution_time_ms", suffix=" ms"),
    ),
    "gcp_cloud_functions": (
        _field("Requests", "monthly_requests", suffix="/month"),
        _field("Memory", "memory_mb", suffix=" MB"),
        _field("CPU", "cpu"),
        _field("Execution", "average_execution_time_ms", suffix=" ms"),
    ),
    "gcp_cloud_run": (
        _field("Requests", "requests_per_month", "monthly_requests", suffix="/month"),
        _field("vCPU", "vcpu"),
        _field("Memory", "memory_gb", suffix=" GB"),
        _field("Execution", "average_execution_time_ms", suffix=" ms"),
    ),
    "azure_functions": (
        _field(
            "Executions",
            "monthly_executions",
            "executions",
            suffix="/month",
        ),
        _field("Memory", "memory_mb", suffix=" MB"),
        _field("Execution", "average_execution_time_ms", suffix=" ms"),
    ),
    "gcp_cloud_sql": (
        _field("CPU", "required_cpu", "cpu"),
        _field("RAM", "required_ram_gb", "ram_gb", suffix=" GB"),
        _field(
            "Database",
            "required_database_storage_gb",
            "database_storage_gb",
            suffix=" GB",
        ),
        _field("Selected package", "selected_sku.name"),
    ),
    "aws_rds": (
        _field("vCPU", "vcpu", "required_vcpu"),
        _field("Memory", "memory_gb", "required_memory_gb", suffix=" GB"),
        _field("Selected package", "selected_sku.name", "selected_instance.name"),
    ),
    "azure_sql_database": (
        _field("vCPU", "vcpu", "required_vcpu"),
        _field("Memory", "memory_gb", "required_memory_gb", suffix=" GB"),
        _field("Selected package", "selected_sku.name"),
    ),
    "aws_s3": (
        _field("Storage", "storage_gb", suffix=" GB"),
        _field("Monthly reads", "read_requests", "monthly_reads", suffix=""),
    ),
    "gcp_cloud_storage": (
        _field("Storage", "storage_gb", suffix=" GB"),
        _field("Monthly reads", "read_requests", "monthly_reads", suffix=""),
    ),
    "azure_blob_storage": (
        _field("Storage", "storage_gb", "billable_storage_gb", suffix=" GB"),
        _field("Monthly reads", "read_requests", "monthly_reads", suffix=""),
    ),
    "aws_ec2": (
        _field("Workload", "workload_type"),
        _field("vCPU", "vcpu"),
        _field("Memory", "memory_gb", suffix=" GB"),
        _field("Hours", "running_hours_per_month", suffix="/month"),
        _field("Selected instance", "selected_sku.name"),
    ),
    "aws_elasticache_memcached": (
        _field("Memory", "memory_gb", "billable_memory_gb", suffix=" GB"),
        _field("Selected node", "selected_sku.name"),
    ),
    "aws_elasticache_redis": (
        _field("Memory", "memory_gb", "billable_memory_gb", suffix=" GB"),
        _field("Selected node", "selected_sku.name"),
    ),
    "azure_cache_for_redis": (
        _field("Memory", "memory_gb", suffix=" GB"),
        _field("Selected tier", "selected_sku.name"),
    ),
    "aws_dynamodb": (
        _field("Reads", "monthly_reads", "reads_per_month", suffix="/month"),
        _field("Writes", "monthly_writes", "writes_per_month", suffix="/month"),
        _field("Storage", "database_storage_gb", suffix=" GB"),
    ),
    "gcp_firestore": (
        _field("Reads", "billable_reads", "reads_per_day", suffix=""),
        _field("Writes", "billable_writes", "writes_per_day", suffix=""),
        _field("Storage", "database_storage_gb", "billable_storage", suffix=" GB"),
    ),
    "azure_cosmos_db": (
        _field("Capacity mode", "capacity_mode", "selected_sku.name"),
        _field("Storage", "database_storage_gb", suffix=" GB"),
        _field(
            "RU/s",
            "required_ru_per_second",
            "billable_ru_per_second",
        ),
        _field("Request units", "request_units_per_month", suffix="/month"),
    ),
    "aws_cognito": (
        _field("Monthly active users", "users", "billable_mau"),
    ),
    "azure_entra_id": (
        _field("Monthly active users", "users", "billable_mau"),
    ),
    "gcp_firebase_auth": (
        _field("Monthly active users", "users", "billable"),
    ),
    "aws_api_gateway": (
        _field("API type", "api_type", "selected_sku.name"),
        _field("Requests", "requests_per_month", "monthly_requests", suffix="/month"),
        _field("Messages", "messages_per_month", suffix="/month"),
    ),
    "gcp_api_gateway": (
        _field("Requests", "requests_per_month", "monthly_requests", suffix="/month"),
    ),
    "azure_api_management": (
        _field("Requests", "monthly_requests", "requests_per_month", suffix="/month"),
    ),
    "aws_sns": (
        _field("Notifications", "notifications", "monthly_notifications", suffix="/month"),
        _field("Channels", "notification_channel_count"),
    ),
    "aws_ses": (
        _field("Emails", "emails", "monthly_emails", suffix="/month"),
    ),
    "aws_sqs": (
        _field("Queue type", "queue_type", "selected_sku.name"),
        _field("Requests", "requests_per_month", "monthly_requests", suffix="/month"),
    ),
    "azure_queue_storage": (
        _field("Messages", "messages_per_month", suffix="/month"),
        _field("Avg message size", "average_message_size_kb", suffix=" KB"),
    ),
    "azure_notification_hubs": (
        _field(
            "Notifications",
            "notifications",
            "monthly_notifications",
            suffix="/month",
        ),
    ),
    "gcp_firebase_messaging": (
        _field("Messages", "messages", "monthly_messages", suffix="/month"),
    ),
    "aws_cloudwatch": (
        _field("Custom metrics", "custom_metrics"),
        _field("Log ingestion", "log_ingestion_gb_per_month", "log_ingestion_gb", suffix=" GB"),
        _field("Alarms", "alarms"),
    ),
    "gcp_cloud_monitoring": (
        _field("Log ingestion", "log_ingestion_gb_per_month", "log_ingestion_gib", suffix=" GB"),
        _field("Metrics", "monitoring_metrics_mib_per_month", suffix=" MiB"),
    ),
    "azure_monitor": (
        _field("Log ingestion", "log_ingestion_gb_per_month", "log_ingestion_gb", suffix=" GB"),
        _field("Alerts", "monitoring_alerts"),
    ),
}

_GENERIC_PRIORITY_FIELDS: tuple[_SummaryField, ...] = (
    _field("Selected package", "selected_sku.name"),
    _field("Capacity mode", "capacity_mode"),
    _field("Requests", "monthly_requests", "requests_per_month", suffix="/month"),
    _field("Storage", "storage_gb", "database_storage_gb", suffix=" GB"),
    _field("Memory", "memory_mb", suffix=" MB"),
    _field("Memory", "memory_gb", "ram_gb", suffix=" GB"),
    _field("CPU", "cpu", "vcpu", "required_cpu"),
    _field("Execution", "average_execution_time_ms", suffix=" ms"),
    _field("Monthly active users", "users"),
)


def _free_tier_applied(
    *,
    locals_snapshot: dict[str, Any],
    free_tier: dict[str, Any],
) -> bool:
    if not free_tier:
        return False

    for key, free_amount in free_tier.items():
        if not isinstance(free_amount, (int, float)) or free_amount <= 0:
            continue
        billable = locals_snapshot.get(f"billable_{key}")
        usage = locals_snapshot.get(key)
        if usage is None:
            # Common alternate names used by scripts.
            usage = locals_snapshot.get(
                {
                    "requests": "monthly_requests",
                    "compute_gb_seconds": "compute_gb_seconds",
                    "monthly_active_users": "users",
                    "data_transfer_out_gb": "data_transfer_out_gb",
                }.get(key, "")
            )
        if isinstance(billable, (int, float)) and isinstance(usage, (int, float)):
            if billable < usage:
                return True
        if isinstance(billable, (int, float)) and billable == 0:
            return True
        if locals_snapshot.get(f"free_{key}") is not None:
            return True

    return any(
        isinstance(value, (int, float)) and value > 0 for value in free_tier.values()
    ) and any(
        key.startswith("billable_") for key in locals_snapshot
    )


def _lines_from_fields(
    fields: tuple[_SummaryField, ...],
    locals_snapshot: dict[str, Any],
) -> list[str]:
    lines: list[str] = []
    seen_labels: set[str] = set()
    for field in fields:
        if field.label in seen_labels:
            continue
        value = _lookup(locals_snapshot, field.keys)
        if value is None:
            continue
        lines.append(f"{field.label}: {field.format_value(value)}")
        seen_labels.add(field.label)
    return lines


def build_calculation_summary(
    *,
    service_id: str | None,
    locals_snapshot: dict[str, Any],
    free_tier: dict[str, Any],
    monthly_price: float,
) -> list[str]:
    """Return short bullets that explain the final monthly price."""

    fields = _SERVICE_SUMMARY_FIELDS.get(service_id or "", ())
    lines = _lines_from_fields(fields, locals_snapshot)

    if not lines:
        lines = _lines_from_fields(_GENERIC_PRIORITY_FIELDS, locals_snapshot)

    if _free_tier_applied(locals_snapshot=locals_snapshot, free_tier=free_tier):
        lines.append("Free tier applied")

    lines.append(f"Price: ${float(monthly_price):.2f}")
    return lines
