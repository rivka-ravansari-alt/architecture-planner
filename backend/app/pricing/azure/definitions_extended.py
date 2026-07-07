"""Azure pricing models for remaining catalog services (hosting, data, observability, etc.)."""

from __future__ import annotations

from app.pricing.schemas import (
    AzureServicePricingModel,
    CalculatedSkuDefinition,
    FreeTierAllowance,
    InputDataType,
    PricingModelDetails,
    UsageInputDefinition,
)

_FREE_TIER_EMPTY = FreeTierAllowance(allowances={}, notes="No always-free tier modeled.")

_AZURE_APP_SERVICE = AzureServicePricingModel(
    cloud="azure",
    service="Azure App Service",
    component_types=["web_app", "admin_panel"],
    catalog_service_name="Azure App Service",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="instance_hours_per_month",
                description="App Service plan instance hours provisioned.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=730,
            ),
            UsageInputDefinition(
                key="requests_per_month",
                description="HTTP requests served by the web app.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer from the app.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="instance_hours",
                description="Billable App Service plan hours.",
                unit="hours/month",
                input_keys=["instance_hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from instance_hours_per_month.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable HTTP requests.",
                unit="requests/month",
                input_keys=["requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"instance_hours_per_month": 730, "requests_per_month": 0, "data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="instance-hours and requests",
        billing_granularity="per hour; per million requests",
        warnings=["Static Web Apps and deployment slots are simplified."],
    ),
)

_AZURE_APP_CENTER = AzureServicePricingModel(
    cloud="azure",
    service="Azure App Center",
    component_types=["mobile_app"],
    catalog_service_name="Azure App Center",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="build_minutes_per_month",
                description="Mobile CI/CD build minutes consumed per month.",
                unit="minutes/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="test_device_minutes_per_month",
                description="Cloud test device minutes per month.",
                unit="minutes/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="build_minutes",
                description="Billable build pipeline minutes.",
                unit="minutes/month",
                input_keys=["build_minutes_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from build_minutes_per_month.",
            ),
            CalculatedSkuDefinition(
                key="test_minutes",
                description="Billable cloud device test minutes.",
                unit="minutes/month",
                input_keys=["test_device_minutes_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from test_device_minutes_per_month.",
            ),
        ],
        default_values={"build_minutes_per_month": 0, "test_device_minutes_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"build_minutes": 240},
            notes="Free tier includes limited build minutes (simplified).",
        ),
        billing_unit="build and test minutes",
        billing_granularity="per minute",
        warnings=["Distribution and crash analytics tiers are simplified."],
    ),
)

_AZURE_COSMOS_DB = AzureServicePricingModel(
    cloud="azure",
    service="Azure Cosmos DB",
    component_types=["database"],
    catalog_service_name="Azure Cosmos DB",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="request_units_per_month",
                description="Total request units (RU/s-seconds) consumed per month.",
                unit="RU/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Stored data volume.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="request_units",
                description="Billable request units.",
                unit="RU/month",
                input_keys=["request_units_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from request_units_per_month.",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Billable stored data.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"request_units": 2_592_000, "storage_gb_month": 25},
            notes="Free tier: 1000 RU/s × 730h and 25 GB storage (simplified).",
        ),
        billing_unit="RU and GB-months",
        billing_granularity="per 100 RU/s-hour; per GB-month",
        warnings=["Serverless vs provisioned throughput modes are simplified."],
    ),
)

_AZURE_REDIS_CACHE = AzureServicePricingModel(
    cloud="azure",
    service="Azure Redis Cache",
    component_types=["cache"],
    catalog_service_name="Redis Cache",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="cache_size",
                description="Cache tier size label (Basic C0, Standard C1, etc.).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Basic C0",
            ),
            UsageInputDefinition(
                key="hours_per_month",
                description="Billable cache instance hours while online.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer from cache nodes.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="instance_hours",
                description="Billable cache instance hours.",
                unit="hours/month",
                input_keys=["hours_per_month", "cache_size"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from hours_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"cache_size": "Basic C0", "hours_per_month": 730, "data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="instance-hours",
        billing_granularity="per hour by cache size",
        warnings=["Cluster and geo-replication multiply instance charges."],
    ),
)

_AZURE_COGNITIVE_SEARCH = AzureServicePricingModel(
    cloud="azure",
    service="Azure Cognitive Search",
    component_types=["search"],
    catalog_service_name="Azure Cognitive Search",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="search_units_hours",
                description="Search unit hours provisioned per month.",
                unit="SU-hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=730,
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Search index storage volume.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound transfer from search service.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="search_unit_hours",
                description="Billable search unit hours.",
                unit="SU-hours/month",
                input_keys=["search_units_hours"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from search_units_hours.",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Billable index storage.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"search_units_hours": 730, "data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="SU-hours and GB-months",
        billing_granularity="per SU-hour; per GB-month",
        warnings=["Semantic ranker and skillset enrichment are not modeled separately."],
    ),
)

_AZURE_FOUNDRY_MODELS = AzureServicePricingModel(
    cloud="azure",
    service="Azure Foundry Models",
    component_types=["ai_provider"],
    catalog_service_name="Foundry Models",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="input_tokens_per_month",
                description="Model input tokens consumed per month.",
                unit="tokens/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="output_tokens_per_month",
                description="Model output tokens generated per month.",
                unit="tokens/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="input_tokens",
                description="Billable input tokens.",
                unit="tokens/month",
                input_keys=["input_tokens_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from input_tokens_per_month.",
            ),
            CalculatedSkuDefinition(
                key="output_tokens",
                description="Billable output tokens.",
                unit="tokens/month",
                input_keys=["output_tokens_per_month"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from output_tokens_per_month.",
            ),
        ],
        default_values={"output_tokens_per_month": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="tokens",
        billing_granularity="per 1K tokens",
        warnings=["Model-specific pricing tiers and PTU are simplified."],
    ),
)

_AZURE_NOTIFICATION_HUBS = AzureServicePricingModel(
    cloud="azure",
    service="Notification Hubs",
    component_types=["notification"],
    catalog_service_name="Notification Hubs",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="push_notifications_per_month",
                description="Push notifications sent per month.",
                unit="notifications/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="namespace_hours_per_month",
                description="Namespace provisioned hours.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=730,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="notifications",
                description="Billable push notifications.",
                unit="notifications/month",
                input_keys=["push_notifications_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from push_notifications_per_month.",
            ),
            CalculatedSkuDefinition(
                key="namespace_hours",
                description="Billable namespace hours.",
                unit="hours/month",
                input_keys=["namespace_hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from namespace_hours_per_month.",
            ),
        ],
        default_values={"namespace_hours_per_month": 730},
        free_tier=FreeTierAllowance(
            allowances={"notifications": 1_000_000},
            notes="Free tier includes 1M push notifications per subscription (simplified).",
        ),
        billing_unit="notifications and namespace hours",
        billing_granularity="per million notifications; per hour",
        warnings=["PNS-specific tiers and geo-replication are simplified."],
    ),
)

_AZURE_VOICE_CORE = AzureServicePricingModel(
    cloud="azure",
    service="Azure Voice Core",
    component_types=["notification"],
    catalog_service_name="Voice Core",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="voice_minutes_per_month",
                description="Voice call minutes per month.",
                unit="minutes/month",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="sms_messages_per_month",
                description="SMS messages sent per month.",
                unit="messages/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="voice_minutes",
                description="Billable voice call minutes.",
                unit="minutes/month",
                input_keys=["voice_minutes_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from voice_minutes_per_month.",
            ),
            CalculatedSkuDefinition(
                key="sms_messages",
                description="Billable SMS messages.",
                unit="messages/month",
                input_keys=["sms_messages_per_month"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from sms_messages_per_month.",
            ),
        ],
        default_values={"sms_messages_per_month": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="minutes and messages",
        billing_granularity="per minute; per message",
        warnings=["Toll-free and international rates are simplified."],
    ),
)

_AZURE_APPLICATION_INSIGHTS = AzureServicePricingModel(
    cloud="azure",
    service="Application Insights",
    component_types=["tracing", "analytics"],
    catalog_service_name="Application Insights",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="telemetry_gb_per_month",
                description="Telemetry data ingested per month.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="log_queries_per_month",
                description="Log Analytics queries executed per month.",
                unit="queries/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="ingestion_gb",
                description="Billable telemetry ingestion.",
                unit="GB/month",
                input_keys=["telemetry_gb_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from telemetry_gb_per_month.",
            ),
            CalculatedSkuDefinition(
                key="queries",
                description="Billable log queries.",
                unit="queries/month",
                input_keys=["log_queries_per_month"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from log_queries_per_month.",
            ),
        ],
        default_values={"log_queries_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"ingestion_gb": 5},
            notes="Free tier: 5 GB telemetry ingestion per month (simplified).",
        ),
        billing_unit="GB ingestion",
        billing_granularity="per GB",
        warnings=["Smart detection and continuous export are not modeled."],
    ),
)

_AZURE_MONITOR = AzureServicePricingModel(
    cloud="azure",
    service="Azure Monitor",
    component_types=["monitoring", "alerting"],
    catalog_service_name="Azure Monitor",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="metrics_count",
                description="Custom metrics published per month.",
                unit="metrics",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="alert_rules_count",
                description="Metric alert rules provisioned.",
                unit="rules",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="api_requests_per_month",
                description="Monitor API requests per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="custom_metrics",
                description="Billable custom metric-months.",
                unit="metric-months",
                input_keys=["metrics_count"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from metrics_count.",
            ),
            CalculatedSkuDefinition(
                key="alert_rules",
                description="Billable alert rule-months.",
                unit="rule-months",
                input_keys=["alert_rules_count"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from alert_rules_count.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable Monitor API requests.",
                unit="requests/month",
                input_keys=["api_requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from api_requests_per_month.",
            ),
        ],
        default_values={"metrics_count": 0, "alert_rules_count": 1, "api_requests_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"custom_metrics": 10, "alert_rules": 10},
            notes="Free tier: 10 custom metrics and 10 alert rules (simplified).",
        ),
        billing_unit="metrics, rules, and API requests",
        billing_granularity="per metric; per rule; per million API requests",
        warnings=["Prometheus metrics and VM insights are simplified."],
    ),
)

_AZURE_LOG_ANALYTICS = AzureServicePricingModel(
    cloud="azure",
    service="Log Analytics",
    component_types=["logging"],
    catalog_service_name="Log Analytics",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="log_ingestion_gb_per_month",
                description="Log data ingested per month.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="log_retention_gb",
                description="Average log data retained during the month.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="ingestion_gb",
                description="Billable log ingestion.",
                unit="GB/month",
                input_keys=["log_ingestion_gb_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from log_ingestion_gb_per_month.",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Billable log retention storage.",
                unit="GB-months",
                input_keys=["log_retention_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from log_retention_gb.",
            ),
        ],
        default_values={"log_retention_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"ingestion_gb": 5},
            notes="Free tier: 5 GB log ingestion per month (simplified).",
        ),
        billing_unit="GB ingestion and GB-months retention",
        billing_granularity="per GB",
        warnings=["Commitment tiers and search jobs are not modeled."],
    ),
)

_AZURE_POWER_BI = AzureServicePricingModel(
    cloud="azure",
    service="Power BI",
    component_types=["analytics"],
    catalog_service_name="Power BI",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="pro_seats",
                description="Power BI Pro seat count.",
                unit="seats",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="premium_capacity_hours",
                description="Premium capacity hours if applicable.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="pro_seats",
                description="Billable Pro seat-months.",
                unit="seat-months",
                input_keys=["pro_seats"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from pro_seats.",
            ),
            CalculatedSkuDefinition(
                key="premium_hours",
                description="Billable Premium capacity hours.",
                unit="hours/month",
                input_keys=["premium_capacity_hours"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from premium_capacity_hours.",
            ),
        ],
        default_values={"pro_seats": 1, "premium_capacity_hours": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="seats and capacity hours",
        billing_granularity="per seat per month; per hour",
        warnings=["Embedded capacity and Fabric SKUs are simplified."],
    ),
)

_AZURE_KEY_VAULT = AzureServicePricingModel(
    cloud="azure",
    service="Azure Key Vault",
    component_types=["secrets"],
    catalog_service_name="Key Vault",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="secrets_count",
                description="Secrets stored during the month.",
                unit="secrets",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="operations_per_month",
                description="Key Vault API operations per month.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="secret_months",
                description="Billable secret-months.",
                unit="secret-months",
                input_keys=["secrets_count"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from secrets_count.",
            ),
            CalculatedSkuDefinition(
                key="operations",
                description="Billable Key Vault operations.",
                unit="operations/month",
                input_keys=["operations_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from operations_per_month.",
            ),
        ],
        default_values={"secrets_count": 1, "operations_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"operations": 10_000},
            notes="Standard tier includes 10K operations per month (simplified).",
        ),
        billing_unit="operations",
        billing_granularity="per 10K operations",
        warnings=["HSM-backed keys and premium vault tiers are not modeled."],
    ),
)

_AZURE_APP_CONFIGURATION = AzureServicePricingModel(
    cloud="azure",
    service="Azure App Configuration",
    component_types=["config"],
    catalog_service_name="App Configuration",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="configuration_stores",
                description="Configuration store instances provisioned.",
                unit="stores",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="requests_per_month",
                description="Configuration read/write requests per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="store_months",
                description="Billable configuration store-months.",
                unit="store-months",
                input_keys=["configuration_stores"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from configuration_stores.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable configuration requests.",
                unit="requests/month",
                input_keys=["requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from requests_per_month.",
            ),
        ],
        default_values={"configuration_stores": 1, "requests_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 10_000},
            notes="Standard tier includes 10K requests per day cap simplified monthly.",
        ),
        billing_unit="stores and requests",
        billing_granularity="per store per month; per 10K requests",
        warnings=["Feature flags and replica stores are simplified."],
    ),
)

EXTENDED_AZURE_PRICING_MODELS: tuple[AzureServicePricingModel, ...] = (
    _AZURE_APP_SERVICE,
    _AZURE_APP_CENTER,
    _AZURE_COSMOS_DB,
    _AZURE_REDIS_CACHE,
    _AZURE_COGNITIVE_SEARCH,
    _AZURE_FOUNDRY_MODELS,
    _AZURE_NOTIFICATION_HUBS,
    _AZURE_VOICE_CORE,
    _AZURE_APPLICATION_INSIGHTS,
    _AZURE_MONITOR,
    _AZURE_LOG_ANALYTICS,
    _AZURE_POWER_BI,
    _AZURE_KEY_VAULT,
    _AZURE_APP_CONFIGURATION,
)
