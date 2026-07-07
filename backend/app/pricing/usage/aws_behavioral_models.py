"""AWS per-user behavioral usage inputs inferred by the LLM."""

from __future__ import annotations

from app.pricing.schemas import InputDataType, UsageInputDefinition
from app.pricing.usage.behavioral_models import (
    ServiceBehavioralModel,
    _float_input,
    _int_input,
)

_LAMBDA_BEHAVIORAL = ServiceBehavioralModel(
    service="Lambda",
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
    config_input_keys=frozenset({"avg_execution_duration_ms", "memory_mb"}),
)

_ECS_FARGATE_BEHAVIORAL = ServiceBehavioralModel(
    service="ECS Fargate",
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
            "min_tasks",
        }
    ),
)

_RDS_BEHAVIORAL = ServiceBehavioralModel(
    service="RDS",
    behavioral_inputs=(),
    config_input_keys=frozenset({"instance_class", "hours_per_month"}),
)

_DYNAMODB_BEHAVIORAL = ServiceBehavioralModel(
    service="DynamoDB",
    behavioral_inputs=(
        _float_input(
            "read_requests_per_user_per_month",
            "On-demand read request units one user generates per month.",
            "requests/user/month",
            min_value=0,
            max_value=100_000,
        ),
        _float_input(
            "write_requests_per_user_per_month",
            "On-demand write request units one user generates per month.",
            "requests/user/month",
            min_value=0,
            max_value=100_000,
        ),
    ),
    config_input_keys=frozenset({"billing_mode"}),
)

_S3_BEHAVIORAL = ServiceBehavioralModel(
    service="S3",
    behavioral_inputs=(),
    config_input_keys=frozenset({"storage_class", "static_storage_gb"}),
)

_SQS_BEHAVIORAL = ServiceBehavioralModel(
    service="SQS",
    behavioral_inputs=(
        _float_input(
            "messages_per_user_per_month",
            "Queue messages triggered per user per month.",
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
    config_input_keys=frozenset({"queue_type"}),
)

_API_GATEWAY_BEHAVIORAL = ServiceBehavioralModel(
    service="API Gateway",
    behavioral_inputs=(
        _float_input(
            "sessions_per_user_per_month",
            "How often one user hits the API gateway per month.",
            "sessions/user/month",
            min_value=0.1,
            max_value=120,
        ),
        _float_input(
            "requests_per_session",
            "API requests one user generates per session through the gateway.",
            "requests/session",
            min_value=1,
            max_value=500,
        ),
        _float_input(
            "avg_response_size_kb",
            "Average response payload size per API request.",
            "KB/request",
            min_value=0.1,
            max_value=10_240,
        ),
    ),
    config_input_keys=frozenset({"api_type"}),
)

_SNS_BEHAVIORAL = ServiceBehavioralModel(
    service="SNS",
    behavioral_inputs=(
        _float_input(
            "messages_per_user_per_month",
            "SNS publish/delivery operations per user per month.",
            "messages/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "avg_message_size_kb",
            "Average SNS message payload size.",
            "KB/message",
            min_value=0.01,
            max_value=1024,
        ),
    ),
    config_input_keys=frozenset(),
)

_CLOUDFRONT_BEHAVIORAL = ServiceBehavioralModel(
    service="CloudFront",
    behavioral_inputs=(
        _float_input(
            "page_views_per_user_per_month",
            "CDN asset/page requests one user generates per month.",
            "views/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "avg_object_size_kb",
            "Average edge object size served per request.",
            "KB/request",
            min_value=0.1,
            max_value=10_240,
        ),
    ),
    config_input_keys=frozenset(),
)

_ALB_BEHAVIORAL = ServiceBehavioralModel(
    service="Application Load Balancer",
    behavioral_inputs=(
        _float_input(
            "requests_per_user_per_month",
            "HTTP requests routed through the load balancer per user per month.",
            "requests/user/month",
            min_value=0,
            max_value=100_000,
        ),
        _float_input(
            "avg_request_size_kb",
            "Average request+response bytes per routed request.",
            "KB/request",
            min_value=0.1,
            max_value=10_240,
        ),
    ),
    config_input_keys=frozenset({"hours_per_month"}),
)

_SECRETS_BEHAVIORAL = ServiceBehavioralModel(
    service="Secrets Manager",
    behavioral_inputs=(
        _float_input(
            "api_calls_per_user_per_month",
            "Secret retrieval API calls attributable to one user per month.",
            "calls/user/month",
            min_value=0,
            max_value=10_000,
        ),
    ),
    config_input_keys=frozenset({"secrets_count"}),
)

from app.pricing.usage.aws_behavioral_models_extended import EXTENDED_AWS_BEHAVIORAL_MODELS

AWS_BEHAVIORAL_MODELS: dict[str, ServiceBehavioralModel] = {
    model.service: model
    for model in (
        _LAMBDA_BEHAVIORAL,
        _ECS_FARGATE_BEHAVIORAL,
        _RDS_BEHAVIORAL,
        _DYNAMODB_BEHAVIORAL,
        _S3_BEHAVIORAL,
        _SQS_BEHAVIORAL,
        _API_GATEWAY_BEHAVIORAL,
        _SNS_BEHAVIORAL,
        _CLOUDFRONT_BEHAVIORAL,
        _ALB_BEHAVIORAL,
        _SECRETS_BEHAVIORAL,
    )
}
AWS_BEHAVIORAL_MODELS.update(EXTENDED_AWS_BEHAVIORAL_MODELS)
