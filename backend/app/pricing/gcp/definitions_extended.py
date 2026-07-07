"""GCP pricing models for analytics, observability, AI, and hosting services."""

from __future__ import annotations

from app.pricing.schemas import (
    CalculatedSkuDefinition,
    FreeTierAllowance,
    GcpServicePricingModel,
    InputDataType,
    PricingModelDetails,
    UsageInputDefinition,
)

_FREE_TIER_EMPTY = FreeTierAllowance(allowances={}, notes="No always-free tier modeled.")

_GCP_BIGQUERY = GcpServicePricingModel(
    cloud="gcp",
    service="BigQuery",
    component_types=["analytics"],
    catalog_service_name="BigQuery",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="data_scanned_tb_per_month",
                description="Data scanned by BigQuery queries per month.",
                unit="TB/month",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Active logical storage for tables.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="data_scanned_tb",
                description="Billable query data scanned.",
                unit="TB/month",
                input_keys=["data_scanned_tb_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from data_scanned_tb_per_month.",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Billable active storage.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
        ],
        default_values={"storage_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"data_scanned_tb": 1, "storage_gb_month": 10},
            notes="GCP Free Tier: 1 TB queries and 10 GB storage per month (simplified).",
        ),
        billing_unit="TB scanned and GB-months",
        billing_granularity="per TB; per GB-month",
        warnings=["Streaming inserts and BI Engine reservations are simplified."],
    ),
)

_GCP_CLOUD_LOGGING = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Logging",
    component_types=["logging"],
    catalog_service_name="Cloud Logging",
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
                key="log_storage_gb",
                description="Average log storage retained during the month.",
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
                description="Billable log storage.",
                unit="GB-months",
                input_keys=["log_storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from log_storage_gb.",
            ),
        ],
        default_values={"log_storage_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"ingestion_gb": 50, "storage_gb_month": 30},
            notes="GCP Free Tier: 50 GB ingestion and 30-day retention (simplified).",
        ),
        billing_unit="GB ingestion and GB-months storage",
        billing_granularity="per GB",
        warnings=["Logs-based metrics and routing sinks are not modeled."],
    ),
)

_GCP_CLOUD_MONITORING = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Monitoring",
    component_types=["monitoring", "alerting", "analytics"],
    catalog_service_name="Cloud Monitoring",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="custom_metrics_count",
                description="Number of custom metrics published per month.",
                unit="metrics",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="api_requests_per_month",
                description="Monitoring API requests per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="alert_policies_count",
                description="Alert policies provisioned during the month.",
                unit="policies",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="custom_metrics",
                description="Billable custom metric-months.",
                unit="metric-months",
                input_keys=["custom_metrics_count"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from custom_metrics_count.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable API requests.",
                unit="requests/month",
                input_keys=["api_requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from api_requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="alert_policies",
                description="Billable alert policy-months.",
                unit="policy-months",
                input_keys=["alert_policies_count"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from alert_policies_count.",
            ),
        ],
        default_values={
            "custom_metrics_count": 0,
            "api_requests_per_month": 0,
            "alert_policies_count": 1,
        },
        free_tier=FreeTierAllowance(
            allowances={"custom_metrics": 150, "requests": 1_000_000},
            notes="GCP Free Tier: 150 custom metrics and 1M API reads (simplified).",
        ),
        billing_unit="metrics, API requests, and alert policies",
        billing_granularity="per metric; per million API requests",
        warnings=["Uptime checks and SLO burn alerts are simplified."],
    ),
)

_GCP_CLOUD_TRACE = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Trace",
    component_types=["tracing"],
    catalog_service_name="Cloud Trace",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="spans_ingested_per_month",
                description="Trace spans recorded and stored per month.",
                unit="spans/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="spans_scanned_per_month",
                description="Spans retrieved via API per month.",
                unit="spans/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="spans_ingested",
                description="Billable spans ingested.",
                unit="spans/month",
                input_keys=["spans_ingested_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from spans_ingested_per_month.",
            ),
            CalculatedSkuDefinition(
                key="spans_scanned",
                description="Billable spans scanned.",
                unit="spans/month",
                input_keys=["spans_scanned_per_month"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from spans_scanned_per_month.",
            ),
        ],
        default_values={"spans_scanned_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"spans_ingested": 2_500_000},
            notes="GCP Free Tier: 2.5M spans ingested per month (simplified).",
        ),
        billing_unit="spans",
        billing_granularity="per million spans",
        warnings=["Sampling and BigQuery export are simplified."],
    ),
)

_GCP_FIREBASE_HOSTING = GcpServicePricingModel(
    cloud="gcp",
    service="Firebase Hosting",
    component_types=["admin_panel", "web_app"],
    catalog_service_name="Firebase Hosting",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="hosting_requests_per_month",
                description="Static and SSR hosting requests per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_transfer_gb",
                description="Hosting data transfer out per month.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable hosting requests.",
                unit="requests/month",
                input_keys=["hosting_requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from hosting_requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable data transfer.",
                unit="GB/month",
                input_keys=["data_transfer_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_transfer_gb.",
            ),
        ],
        default_values={"data_transfer_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 10_000_000, "egress_gb": 360},
            notes="Spark plan: 10 GB storage and 360 MB/day transfer (simplified monthly).",
        ),
        billing_unit="requests and GB transfer",
        billing_granularity="per million requests; per GB",
        warnings=["Cloud Functions for Firebase SSR billed separately."],
    ),
)

_GCP_GEMINI_API = GcpServicePricingModel(
    cloud="gcp",
    service="Gemini API",
    component_types=["ai_provider"],
    catalog_service_name="Gemini API",
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
        warnings=["Model-specific pricing tiers and context caching are simplified."],
    ),
)

_GCP_VERTEX_AI = GcpServicePricingModel(
    cloud="gcp",
    service="Vertex AI",
    component_types=["ai_provider"],
    catalog_service_name="Vertex AI",
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
            UsageInputDefinition(
                key="prediction_hours_per_month",
                description="Dedicated prediction node-hours per month.",
                unit="hours/month",
                data_type=InputDataType.float,
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
            CalculatedSkuDefinition(
                key="prediction_hours",
                description="Billable dedicated prediction hours.",
                unit="hours/month",
                input_keys=["prediction_hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from prediction_hours_per_month.",
            ),
        ],
        default_values={"output_tokens_per_month": 0, "prediction_hours_per_month": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="tokens and node-hours",
        billing_granularity="per 1K tokens; per hour",
        warnings=["Training jobs and feature store are not modeled separately."],
    ),
)

_GCP_VERTEX_AI_SEARCH = GcpServicePricingModel(
    cloud="gcp",
    service="Vertex AI Search",
    component_types=["search"],
    catalog_service_name="Vertex AI Search",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="search_queries_per_month",
                description="Search queries executed per month.",
                unit="queries/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Indexed document storage volume.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound transfer from search domain.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable search queries.",
                unit="queries/month",
                input_keys=["search_queries_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from search_queries_per_month.",
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
        default_values={"data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="queries and GB-months",
        billing_granularity="per 1K queries; per GB-month",
        warnings=["Enterprise search licensing and grounding are simplified."],
    ),
)

EXTENDED_GCP_PRICING_MODELS: tuple[GcpServicePricingModel, ...] = (
    _GCP_BIGQUERY,
    _GCP_CLOUD_LOGGING,
    _GCP_CLOUD_MONITORING,
    _GCP_CLOUD_TRACE,
    _GCP_FIREBASE_HOSTING,
    _GCP_GEMINI_API,
    _GCP_VERTEX_AI,
    _GCP_VERTEX_AI_SEARCH,
)
