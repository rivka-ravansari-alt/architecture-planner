"""Minimal behavioral models for extended Azure catalog services."""

from __future__ import annotations

from app.pricing.usage.behavioral_models import ServiceBehavioralModel, _float_input, _int_input

_EXTENDED_AZURE_BEHAVIORAL: tuple[ServiceBehavioralModel, ...] = (
    ServiceBehavioralModel(
        service="API Management",
        behavioral_inputs=(
            _float_input(
                "sessions_per_user_per_month",
                "How often one user triggers API gateway traffic per month.",
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
        ),
        config_input_keys=frozenset({"sku_tier"}),
    ),
    ServiceBehavioralModel(
        service="Application Gateway",
        behavioral_inputs=(),
        config_input_keys=frozenset({"hours_per_month"}),
    ),
    ServiceBehavioralModel(
        service="Content Delivery Network",
        behavioral_inputs=(
            _float_input(
                "page_views_per_user_per_month",
                "Static asset page views per user per month.",
                "views/user/month",
                min_value=0,
                max_value=500,
            ),
            _float_input(
                "avg_asset_size_kb",
                "Average CDN asset size per view.",
                "KB/view",
                min_value=1,
                max_value=5120,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Azure App Service",
        behavioral_inputs=(
            _float_input(
                "sessions_per_user_per_month",
                "How often one user loads the web app per month.",
                "sessions/user/month",
                min_value=0.1,
                max_value=120,
            ),
            _float_input(
                "requests_per_session",
                "HTTP requests one user generates per session.",
                "requests/session",
                min_value=1,
                max_value=200,
            ),
        ),
        config_input_keys=frozenset({"instance_hours_per_month"}),
    ),
    ServiceBehavioralModel(
        service="Azure App Center",
        behavioral_inputs=(
            _float_input(
                "builds_per_month",
                "Mobile CI builds triggered per month.",
                "builds/month",
                min_value=0,
                max_value=500,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Azure Cosmos DB",
        behavioral_inputs=(
            _float_input(
                "reads_per_user_per_month",
                "Document read operations per user per month.",
                "reads/user/month",
                min_value=0,
                max_value=50_000,
            ),
            _float_input(
                "writes_per_user_per_month",
                "Document write operations per user per month.",
                "writes/user/month",
                min_value=0,
                max_value=10_000,
            ),
            _float_input(
                "storage_kb_per_user",
                "Stored document data per user.",
                "KB/user",
                min_value=0,
                max_value=10_240,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Azure Redis Cache",
        behavioral_inputs=(),
        config_input_keys=frozenset({"cache_size", "hours_per_month"}),
    ),
    ServiceBehavioralModel(
        service="Azure Cognitive Search",
        behavioral_inputs=(
            _float_input(
                "searches_per_user_per_month",
                "Search queries one user runs per month.",
                "searches/user/month",
                min_value=0,
                max_value=5000,
            ),
            _float_input(
                "indexed_kb_per_user",
                "Search index size attributable to one user.",
                "KB/user",
                min_value=0,
                max_value=5120,
            ),
        ),
        config_input_keys=frozenset({"search_units_hours"}),
    ),
    ServiceBehavioralModel(
        service="Azure Foundry Models",
        behavioral_inputs=(
            _int_input(
                "input_tokens_per_user_per_month",
                "Model input tokens one user consumes per month.",
                "tokens/user/month",
                min_value=0,
                max_value=5_000_000,
            ),
            _int_input(
                "output_tokens_per_user_per_month",
                "Model output tokens one user generates per month.",
                "tokens/user/month",
                min_value=0,
                max_value=2_000_000,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Notification Hubs",
        behavioral_inputs=(
            _float_input(
                "notifications_per_user_per_month",
                "Push notifications sent to one user per month.",
                "notifications/user/month",
                min_value=0,
                max_value=500,
            ),
        ),
        config_input_keys=frozenset({"namespace_hours_per_month"}),
    ),
    ServiceBehavioralModel(
        service="Azure Voice Core",
        behavioral_inputs=(
            _float_input(
                "voice_minutes_per_user_per_month",
                "Voice call minutes attributable to one user per month.",
                "minutes/user/month",
                min_value=0,
                max_value=60,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Application Insights",
        behavioral_inputs=(
            _float_input(
                "telemetry_kb_per_user_per_month",
                "Telemetry data generated per user per month.",
                "KB/user/month",
                min_value=0,
                max_value=10_240,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Azure Monitor",
        behavioral_inputs=(),
        config_input_keys=frozenset({"metrics_count", "alert_rules_count"}),
    ),
    ServiceBehavioralModel(
        service="Log Analytics",
        behavioral_inputs=(
            _float_input(
                "log_kb_per_user_per_month",
                "Log volume generated per user per month.",
                "KB/user/month",
                min_value=0,
                max_value=5120,
            ),
        ),
        config_input_keys=frozenset(),
    ),
    ServiceBehavioralModel(
        service="Power BI",
        behavioral_inputs=(),
        config_input_keys=frozenset({"pro_seats", "premium_capacity_hours"}),
    ),
    ServiceBehavioralModel(
        service="Azure Key Vault",
        behavioral_inputs=(
            _float_input(
                "secret_reads_per_user_per_month",
                "Secret retrieval operations per user per month.",
                "reads/user/month",
                min_value=0,
                max_value=1000,
            ),
        ),
        config_input_keys=frozenset({"secrets_count"}),
    ),
    ServiceBehavioralModel(
        service="Azure App Configuration",
        behavioral_inputs=(
            _float_input(
                "config_reads_per_user_per_month",
                "Configuration read operations per user per month.",
                "reads/user/month",
                min_value=0,
                max_value=500,
            ),
        ),
        config_input_keys=frozenset({"configuration_stores"}),
    ),
)

EXTENDED_AZURE_BEHAVIORAL_MODELS: dict[str, ServiceBehavioralModel] = {
    model.service: model for model in _EXTENDED_AZURE_BEHAVIORAL
}
