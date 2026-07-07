"""Per-user behavioral usage inputs inferred by the LLM.

The LLM infers behavioral characteristics (one user's patterns). A deterministic
scaling step converts them into project-level billing inputs using expected_users.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.pricing.schemas import InputDataType, UsageInputDefinition

_KB_PER_GB = 1024 * 1024


@dataclass(frozen=True)
class ServiceBehavioralModel:
    """Behavioral and config inputs for one Azure service."""

    service: str
    behavioral_inputs: tuple[UsageInputDefinition, ...]
    config_input_keys: frozenset[str]


def _int_input(
    key: str,
    description: str,
    unit: str,
    *,
    min_value: int | float = 0,
    max_value: int | float | None = None,
    default_value: int | float | None = None,
) -> UsageInputDefinition:
    return UsageInputDefinition(
        key=key,
        description=description,
        unit=unit,
        data_type=InputDataType.integer,
        min_value=min_value,
        max_value=max_value,
        default_value=default_value,
    )


def _float_input(
    key: str,
    description: str,
    unit: str,
    *,
    min_value: int | float = 0,
    max_value: int | float | None = None,
    default_value: int | float | None = None,
) -> UsageInputDefinition:
    return UsageInputDefinition(
        key=key,
        description=description,
        unit=unit,
        data_type=InputDataType.float,
        min_value=min_value,
        max_value=max_value,
        default_value=default_value,
    )


_CONTAINER_APPS_BEHAVIORAL = ServiceBehavioralModel(
    service="Azure Container Apps",
    behavioral_inputs=(
        _float_input(
            "sessions_per_user_per_month",
            "How often one user opens the app per month.",
            "sessions/user/month",
            min_value=0.1,
            max_value=120,
        ),
        _float_input(
            "requests_per_session",
            "API requests one user generates per session.",
            "requests/session",
            min_value=1,
            max_value=500,
        ),
        _float_input(
            "avg_response_size_kb",
            "Average outbound response size per API request.",
            "KB/request",
            min_value=0.1,
            max_value=10_240,
        ),
    ),
    config_input_keys=frozenset(
        {
            "avg_request_duration_seconds",
            "cpu",
            "memory_gb",
            "min_replicas",
            "max_replicas",
        }
    ),
)

_FUNCTIONS_BEHAVIORAL = ServiceBehavioralModel(
    service="Azure Functions",
    behavioral_inputs=(
        _float_input(
            "sessions_per_user_per_month",
            "How often one user triggers function-backed flows per month.",
            "sessions/user/month",
            min_value=0.1,
            max_value=120,
        ),
        _float_input(
            "invocations_per_session",
            "Function invocations one user triggers per session.",
            "invocations/session",
            min_value=1,
            max_value=500,
        ),
        _float_input(
            "avg_response_size_kb",
            "Average outbound payload per invocation.",
            "KB/invocation",
            min_value=0.1,
            max_value=10_240,
        ),
    ),
    config_input_keys=frozenset(
        {"plan", "avg_execution_duration_ms", "memory_mb"}
    ),
)

_SQL_BEHAVIORAL = ServiceBehavioralModel(
    service="Azure SQL Database",
    behavioral_inputs=(),
    config_input_keys=frozenset(
        {"tier", "compute_model", "vcores", "hours_per_month"}
    ),
)

_BLOB_BEHAVIORAL = ServiceBehavioralModel(
    service="Azure Blob Storage",
    behavioral_inputs=(),
    config_input_keys=frozenset(
        {"access_tier", "redundancy", "list_operations", "static_storage_gb"}
    ),
)

_QUEUE_BEHAVIORAL = ServiceBehavioralModel(
    service="Azure Queue Storage",
    behavioral_inputs=(
        _float_input(
            "messages_per_user_per_month",
            "Queue messages triggered per user per month (notifications, jobs, etc.).",
            "messages/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "avg_message_size_kb",
            "Average payload size per queued message.",
            "KB/message",
            min_value=0.01,
            max_value=1024,
        ),
    ),
    config_input_keys=frozenset(),
)

_SERVICE_BUS_BEHAVIORAL = ServiceBehavioralModel(
    service="Azure Service Bus",
    behavioral_inputs=(
        _float_input(
            "messages_per_user_per_month",
            "Messaging operations attributable to one user per month.",
            "messages/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "avg_message_size_kb",
            "Average payload size per message.",
            "KB/message",
            min_value=0.01,
            max_value=1024,
        ),
        _float_input(
            "concurrent_connections_per_100_users",
            "Peak concurrent brokered connections per 100 users.",
            "connections/100 users",
            min_value=0,
            max_value=1000,
        ),
    ),
    config_input_keys=frozenset(
        {"messaging_tier", "hours_per_month", "messaging_units"}
    ),
)

from app.pricing.usage.aws_behavioral_models import AWS_BEHAVIORAL_MODELS
from app.pricing.usage.azure_extended_behavioral_models import EXTENDED_AZURE_BEHAVIORAL_MODELS
from app.pricing.usage.gcp_behavioral_models import GCP_BEHAVIORAL_MODELS

AZURE_BEHAVIORAL_MODELS: dict[str, ServiceBehavioralModel] = {
    model.service: model
    for model in (
        _CONTAINER_APPS_BEHAVIORAL,
        _FUNCTIONS_BEHAVIORAL,
        _SQL_BEHAVIORAL,
        _BLOB_BEHAVIORAL,
        _QUEUE_BEHAVIORAL,
        _SERVICE_BUS_BEHAVIORAL,
    )
} | EXTENDED_AZURE_BEHAVIORAL_MODELS

BEHAVIORAL_MODELS: dict[str, ServiceBehavioralModel] = {
    **AZURE_BEHAVIORAL_MODELS,
    **AWS_BEHAVIORAL_MODELS,
    **GCP_BEHAVIORAL_MODELS,
}


def get_behavioral_model(
    service: str,
    *,
    provider: str | None = None,
) -> ServiceBehavioralModel | None:
    if provider == "aws":
        return AWS_BEHAVIORAL_MODELS.get(service)
    if provider == "azure":
        return AZURE_BEHAVIORAL_MODELS.get(service)
    if provider == "gcp":
        return GCP_BEHAVIORAL_MODELS.get(service)
    return BEHAVIORAL_MODELS.get(service)
