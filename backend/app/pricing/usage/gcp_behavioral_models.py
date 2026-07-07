"""GCP per-user behavioral usage inputs inferred by the LLM."""

from __future__ import annotations

from app.pricing.usage.behavioral_models import (
    ServiceBehavioralModel,
    _float_input,
)

_CLOUD_RUN_FUNCTIONS_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Run Functions",
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

_CLOUD_RUN_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Run",
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
            "min_instances",
        }
    ),
)

_CLOUD_SQL_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud SQL",
    behavioral_inputs=(),
    config_input_keys=frozenset({"instance_tier", "hours_per_month"}),
)

_CLOUD_FIRESTORE_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Firestore",
    behavioral_inputs=(
        _float_input(
            "read_requests_per_user_per_month",
            "Document reads one user generates per month.",
            "reads/user/month",
            min_value=0,
            max_value=100_000,
        ),
        _float_input(
            "write_requests_per_user_per_month",
            "Document writes one user generates per month.",
            "writes/user/month",
            min_value=0,
            max_value=100_000,
        ),
    ),
    config_input_keys=frozenset({}),
)

_CLOUD_STORAGE_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Storage",
    behavioral_inputs=(),
    config_input_keys=frozenset({"storage_class", "static_storage_gb"}),
)

_CLOUD_PUBSUB_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Pub/Sub",
    behavioral_inputs=(
        _float_input(
            "messages_per_user_per_month",
            "Pub/Sub messages triggered per user per month.",
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
    ),
    config_input_keys=frozenset({}),
)

_CLOUD_TASKS_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Tasks",
    behavioral_inputs=(
        _float_input(
            "tasks_per_user_per_month",
            "Cloud Tasks enqueued per user per month.",
            "tasks/user/month",
            min_value=0,
            max_value=10_000,
        ),
    ),
    config_input_keys=frozenset({}),
)

_CLOUD_MEMORYSTORE_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Memorystore for Redis",
    behavioral_inputs=(),
    config_input_keys=frozenset({"node_tier", "hours_per_month"}),
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
    ),
    config_input_keys=frozenset({}),
)

_SECRET_MANAGER_BEHAVIORAL = ServiceBehavioralModel(
    service="Secret Manager",
    behavioral_inputs=(
        _float_input(
            "api_calls_per_user_per_month",
            "Secret access API calls attributable to one user per month.",
            "calls/user/month",
            min_value=0,
            max_value=10_000,
        ),
    ),
    config_input_keys=frozenset({"secrets_count"}),
)

_NETWORKING_BEHAVIORAL = ServiceBehavioralModel(
    service="Networking",
    behavioral_inputs=(
        _float_input(
            "page_views_per_user_per_month",
            "CDN or LB requests one user generates per month.",
            "views/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "avg_object_size_kb",
            "Average bytes transferred per request.",
            "KB/request",
            min_value=0.1,
            max_value=10_240,
        ),
    ),
    config_input_keys=frozenset({"networking_mode", "lb_hours_per_month"}),
)

_FIREBASE_BEHAVIORAL = ServiceBehavioralModel(
    service="Firebase",
    behavioral_inputs=(
        _float_input(
            "sessions_per_user_per_month",
            "App sessions driving Firebase requests per user per month.",
            "sessions/user/month",
            min_value=0.1,
            max_value=120,
        ),
        _float_input(
            "requests_per_session",
            "Hosting/FCM requests one user generates per session.",
            "requests/session",
            min_value=1,
            max_value=500,
        ),
    ),
    config_input_keys=frozenset({}),
)

_FIREBASE_HOSTING_BEHAVIORAL = ServiceBehavioralModel(
    service="Firebase Hosting",
    behavioral_inputs=_FIREBASE_BEHAVIORAL.behavioral_inputs,
    config_input_keys=frozenset({}),
)

_BIGQUERY_BEHAVIORAL = ServiceBehavioralModel(
    service="BigQuery",
    behavioral_inputs=(
        _float_input(
            "analytics_queries_per_user_per_month",
            "Ad-hoc BigQuery queries one user runs per month.",
            "queries/user/month",
            min_value=0,
            max_value=1_000,
        ),
        _float_input(
            "avg_tb_scanned_per_query",
            "Average terabytes scanned per query.",
            "TB/query",
            min_value=0.0001,
            max_value=100,
        ),
    ),
    config_input_keys=frozenset({}),
)

_CLOUD_LOGGING_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Logging",
    behavioral_inputs=(
        _float_input(
            "log_events_per_user_per_month",
            "Log events generated by one user per month.",
            "events/user/month",
            min_value=0,
            max_value=100_000,
        ),
        _float_input(
            "avg_log_event_kb",
            "Average log event payload size.",
            "KB/event",
            min_value=0.01,
            max_value=64,
        ),
    ),
    config_input_keys=frozenset({}),
)

_CLOUD_MONITORING_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Monitoring",
    behavioral_inputs=(
        _float_input(
            "api_calls_per_user_per_month",
            "Monitoring API calls attributable to one user per month.",
            "calls/user/month",
            min_value=0,
            max_value=10_000,
        ),
    ),
    config_input_keys=frozenset({"custom_metrics_count", "alert_policies_count"}),
)

_CLOUD_TRACE_BEHAVIORAL = ServiceBehavioralModel(
    service="Cloud Trace",
    behavioral_inputs=(
        _float_input(
            "traced_requests_per_user_per_month",
            "Sampled traced spans attributable to one user per month.",
            "spans/user/month",
            min_value=0,
            max_value=10_000,
        ),
    ),
    config_input_keys=frozenset({}),
)

_GEMINI_API_BEHAVIORAL = ServiceBehavioralModel(
    service="Gemini API",
    behavioral_inputs=(
        _float_input(
            "ai_calls_per_user_per_month",
            "Gemini API invocations one user triggers per month.",
            "calls/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "avg_input_tokens_per_call",
            "Average input tokens per Gemini invocation.",
            "tokens/call",
            min_value=1,
            max_value=100_000,
        ),
        _float_input(
            "avg_output_tokens_per_call",
            "Average output tokens per Gemini invocation.",
            "tokens/call",
            min_value=0,
            max_value=100_000,
        ),
    ),
    config_input_keys=frozenset({}),
)

_VERTEX_AI_BEHAVIORAL = ServiceBehavioralModel(
    service="Vertex AI",
    behavioral_inputs=_GEMINI_API_BEHAVIORAL.behavioral_inputs,
    config_input_keys=frozenset({"prediction_hours_per_month"}),
)

_VERTEX_AI_SEARCH_BEHAVIORAL = ServiceBehavioralModel(
    service="Vertex AI Search",
    behavioral_inputs=(
        _float_input(
            "search_queries_per_user_per_month",
            "Search queries one user runs per month.",
            "queries/user/month",
            min_value=0,
            max_value=10_000,
        ),
        _float_input(
            "index_operations_per_user_per_month",
            "Index writes/updates attributable to one user per month.",
            "ops/user/month",
            min_value=0,
            max_value=10_000,
        ),
    ),
    config_input_keys=frozenset({}),
)

GCP_BEHAVIORAL_MODELS: dict[str, ServiceBehavioralModel] = {
    model.service: model
    for model in (
        _CLOUD_RUN_FUNCTIONS_BEHAVIORAL,
        _CLOUD_RUN_BEHAVIORAL,
        _CLOUD_SQL_BEHAVIORAL,
        _CLOUD_FIRESTORE_BEHAVIORAL,
        _CLOUD_STORAGE_BEHAVIORAL,
        _CLOUD_PUBSUB_BEHAVIORAL,
        _CLOUD_TASKS_BEHAVIORAL,
        _CLOUD_MEMORYSTORE_BEHAVIORAL,
        _API_GATEWAY_BEHAVIORAL,
        _SECRET_MANAGER_BEHAVIORAL,
        _NETWORKING_BEHAVIORAL,
        _FIREBASE_BEHAVIORAL,
        _FIREBASE_HOSTING_BEHAVIORAL,
        _BIGQUERY_BEHAVIORAL,
        _CLOUD_LOGGING_BEHAVIORAL,
        _CLOUD_MONITORING_BEHAVIORAL,
        _CLOUD_TRACE_BEHAVIORAL,
        _GEMINI_API_BEHAVIORAL,
        _VERTEX_AI_BEHAVIORAL,
        _VERTEX_AI_SEARCH_BEHAVIORAL,
    )
}
