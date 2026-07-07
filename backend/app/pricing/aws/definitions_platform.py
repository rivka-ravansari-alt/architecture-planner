"""AWS pricing models for platform edge services (API Gateway, CDN, LB, messaging, secrets)."""

from __future__ import annotations

from app.pricing.schemas import (
    AwsServicePricingModel,
    CalculatedSkuDefinition,
    FreeTierAllowance,
    InputDataType,
    PricingModelDetails,
    ResourceRules,
    UsageInputDefinition,
)

_AWS_API_GATEWAY = AwsServicePricingModel(
    cloud="aws",
    service="API Gateway",
    component_types=["api_gateway"],
    catalog_service_name="API Gateway",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="requests_per_month",
                description="HTTP API or REST API requests handled per month.",
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
            UsageInputDefinition(
                key="api_type",
                description="HTTP API or REST API.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="HTTP",
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable API requests.",
                unit="requests/month",
                input_keys=["requests_per_month", "api_type"],
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
        default_values={"api_type": "HTTP", "data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 1_000_000},
            notes="AWS Free Tier: 1M REST/HTTP API calls per month for 12 months.",
        ),
        billing_unit="requests",
        billing_granularity="per million requests",
        warnings=["WebSocket minutes and caching are not modeled."],
    ),
)

_AWS_SNS = AwsServicePricingModel(
    cloud="aws",
    service="SNS",
    component_types=["notification", "alerting"],
    catalog_service_name="SNS",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="messages_per_month",
                description="Publish and delivery operations per month.",
                unit="messages/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Payload egress for SNS deliveries.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable publish/delivery requests.",
                unit="messages/month",
                input_keys=["messages_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from messages_per_month.",
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
            allowances={"requests": 1_000_000},
            notes="AWS Free Tier: 1M SNS publishes per month.",
        ),
        billing_unit="requests",
        billing_granularity="per million requests",
        warnings=["SMS and email delivery tiers are not modeled separately."],
    ),
)

_AWS_CLOUDFRONT = AwsServicePricingModel(
    cloud="aws",
    service="CloudFront",
    component_types=["cdn"],
    catalog_service_name="CloudFront",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="requests_per_month",
                description="HTTP/HTTPS edge requests served per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_transfer_gb",
                description="Edge data transfer out to viewers.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable edge HTTP/HTTPS requests.",
                unit="requests/month",
                input_keys=["requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable edge data transfer.",
                unit="GB/month",
                input_keys=["data_transfer_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_transfer_gb.",
            ),
        ],
        default_values={"data_transfer_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={},
            notes="CloudFront has no always-free tier; AWS Free Tier credits may apply separately.",
        ),
        billing_unit="requests and GB transfer",
        billing_granularity="per 10K requests; per GB egress",
        warnings=["Regional price tiers and origin shield are simplified."],
    ),
)

_AWS_ALB = AwsServicePricingModel(
    cloud="aws",
    service="Application Load Balancer",
    component_types=["load_balancer"],
    catalog_service_name="Application Load Balancer",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="hours_per_month",
                description="Hours the load balancer is provisioned.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
            UsageInputDefinition(
                key="lcu_hours_per_month",
                description="Load Balancer Capacity Unit-hours consumed.",
                unit="LCU-hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer through the load balancer.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="lb_hours",
                description="Billable load balancer hours.",
                unit="hours/month",
                input_keys=["hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from hours_per_month.",
            ),
            CalculatedSkuDefinition(
                key="lcu_hours",
                description="Billable LCU-hours.",
                unit="LCU-hours/month",
                input_keys=["lcu_hours_per_month"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from lcu_hours_per_month.",
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
        default_values={
            "hours_per_month": 730,
            "lcu_hours_per_month": 0,
            "data_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={},
            notes="Application Load Balancer has no always-free tier.",
        ),
        billing_unit="hours and LCU-hours",
        billing_granularity="per hour; per LCU-hour",
        warnings=["LCU dimensions are estimated from request volume; multi-AZ doubles hourly cost."],
    ),
)

_AWS_SECRETS_MANAGER = AwsServicePricingModel(
    cloud="aws",
    service="Secrets Manager",
    component_types=["secrets"],
    catalog_service_name="Secrets Manager",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="secrets_count",
                description="Number of secrets stored during the month.",
                unit="secrets",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="api_calls_per_month",
                description="GetSecretValue and related API calls.",
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
                description="Secrets Manager API calls.",
                unit="operations/month",
                input_keys=["api_calls_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from api_calls_per_month.",
            ),
        ],
        default_values={"secrets_count": 1, "api_calls_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={},
            notes="Secrets Manager has no always-free tier.",
        ),
        billing_unit="secret-months and API calls",
        billing_granularity="per secret per month; per 10K API calls",
        warnings=["Rotation Lambda invocations billed separately."],
    ),
)

PLATFORM_AWS_PRICING_MODELS: tuple[AwsServicePricingModel, ...] = (
    _AWS_API_GATEWAY,
    _AWS_SNS,
    _AWS_CLOUDFRONT,
    _AWS_ALB,
    _AWS_SECRETS_MANAGER,
)
