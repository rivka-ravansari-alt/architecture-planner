"""GCP pricing models for platform edge services (API Gateway, networking, secrets, Firebase)."""

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

_GCP_API_GATEWAY = GcpServicePricingModel(
    cloud="gcp",
    service="API Gateway",
    component_types=["api_gateway"],
    catalog_service_name="API Gateway",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="requests_per_month",
                description="HTTP API requests handled per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Response payload egress through API Gateway.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable API requests.",
                unit="requests/month",
                input_keys=["requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound data transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 2_000_000},
            notes="GCP Free Tier: 2M API calls per month (simplified).",
        ),
        billing_unit="requests",
        billing_granularity="per million requests",
        warnings=["gRPC streaming and API keys are not modeled separately."],
    ),
)

_GCP_SECRET_MANAGER = GcpServicePricingModel(
    cloud="gcp",
    service="Secret Manager",
    component_types=["secrets"],
    catalog_service_name="Secret Manager",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="secrets_count",
                description="Number of secret versions stored during the month.",
                unit="secrets",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="api_calls_per_month",
                description="AccessSecretVersion and related API calls.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="secret_months",
                description="Secret storage (secrets × month).",
                unit="secret-months",
                input_keys=["secrets_count"],
                catalog_sku_roles=["storage"],
                derivation="secrets_count (one secret-month each).",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Secret Manager API calls.",
                unit="operations/month",
                input_keys=["api_calls_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from api_calls_per_month.",
            ),
        ],
        default_values={"secrets_count": 1, "api_calls_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"secret_months": 6, "requests": 10_000},
            notes="GCP Free Tier: 6 active secret versions and 10K access operations (simplified).",
        ),
        billing_unit="secret-months and API calls",
        billing_granularity="per secret version per month; per 10K API calls",
        warnings=["Rotation Cloud Functions billed separately."],
    ),
)

_GCP_NETWORKING = GcpServicePricingModel(
    cloud="gcp",
    service="Networking",
    component_types=["cdn", "load_balancer"],
    catalog_service_name="Networking",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="requests_per_month",
                description="HTTP/HTTPS edge or load-balancer requests per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_transfer_gb",
                description="Edge or load-balancer data transfer out.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="lb_hours_per_month",
                description="Hours a load balancer forwarding rule is provisioned.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
            UsageInputDefinition(
                key="networking_mode",
                description="cdn, load_balancer, or combined.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="cdn",
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable HTTP/HTTPS requests.",
                unit="requests/month",
                input_keys=["requests_per_month", "networking_mode"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable data transfer.",
                unit="GB/month",
                input_keys=["data_transfer_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_transfer_gb.",
            ),
            CalculatedSkuDefinition(
                key="lb_hours",
                description="Billable load balancer hours.",
                unit="hours/month",
                input_keys=["lb_hours_per_month", "networking_mode"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from lb_hours_per_month.",
            ),
        ],
        default_values={
            "data_transfer_gb": 0,
            "lb_hours_per_month": 730,
            "networking_mode": "cdn",
        },
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="requests, GB transfer, and LB hours",
        billing_granularity="per million requests; per GB; per hour",
        warnings=["Cloud CDN, Cloud Load Balancing, and Premium Tier egress are simplified."],
    ),
)

_GCP_FIREBASE = GcpServicePricingModel(
    cloud="gcp",
    service="Firebase",
    component_types=["mobile_app", "web_app", "notification"],
    catalog_service_name="Firebase",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="hosting_requests_per_month",
                description="Firebase Hosting and dynamic content requests per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_transfer_gb",
                description="Hosting and notification payload egress.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="messages_per_month",
                description="FCM push notification deliveries per month.",
                unit="messages/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable hosting and notification requests.",
                unit="requests/month",
                input_keys=["hosting_requests_per_month", "messages_per_month"],
                catalog_sku_roles=["requests"],
                derivation="hosting_requests_per_month + messages_per_month.",
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
        default_values={"data_transfer_gb": 0, "messages_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 10_000_000},
            notes="Spark plan free quotas simplified as monthly request allowance.",
        ),
        billing_unit="requests and GB transfer",
        billing_granularity="per million requests; per GB",
        warnings=["Blaze plan passthrough to underlying GCP services is simplified."],
    ),
)

PLATFORM_GCP_PRICING_MODELS: tuple[GcpServicePricingModel, ...] = (
    _GCP_API_GATEWAY,
    _GCP_SECRET_MANAGER,
    _GCP_NETWORKING,
    _GCP_FIREBASE,
)
