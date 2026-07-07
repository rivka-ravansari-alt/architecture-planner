"""AWS pricing models for remaining catalog services (observability, analytics, hosting, etc.)."""

from __future__ import annotations

from app.pricing.schemas import (
    AwsServicePricingModel,
    CalculatedSkuDefinition,
    FreeTierAllowance,
    InputDataType,
    PricingModelDetails,
    UsageInputDefinition,
)

_FREE_TIER_EMPTY = FreeTierAllowance(allowances={}, notes="No always-free tier modeled.")

_AWS_AMPLIFY = AwsServicePricingModel(
    cloud="aws",
    service="Amplify",
    component_types=["mobile_app", "web_app"],
    catalog_service_name="Amplify",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="build_minutes_per_month",
                description="CI/CD build minutes consumed per month.",
                unit="minutes/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="hosting_requests_per_month",
                description="SSR and static hosting requests served per month.",
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
                key="build_minutes",
                description="Billable build pipeline minutes.",
                unit="minutes/month",
                input_keys=["build_minutes_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from build_minutes_per_month.",
            ),
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
                description="Billable hosting data transfer.",
                unit="GB/month",
                input_keys=["data_transfer_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_transfer_gb.",
            ),
        ],
        default_values={"build_minutes_per_month": 0, "data_transfer_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="build minutes and requests",
        billing_granularity="per minute; per million requests",
        warnings=["SSR compute and WAF are not modeled separately."],
    ),
)

_AWS_AMPLIFY_HOSTING = AwsServicePricingModel(
    cloud="aws",
    service="Amplify Hosting",
    component_types=["admin_panel", "web_app"],
    catalog_service_name="Amplify Hosting",
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
            UsageInputDefinition(
                key="build_minutes_per_month",
                description="Optional build minutes for admin/web deploys.",
                unit="minutes/month",
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
            CalculatedSkuDefinition(
                key="build_minutes",
                description="Billable build minutes.",
                unit="minutes/month",
                input_keys=["build_minutes_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from build_minutes_per_month.",
            ),
        ],
        default_values={"data_transfer_gb": 0, "build_minutes_per_month": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="requests and GB transfer",
        billing_granularity="per million requests; per GB",
        warnings=["Build pipeline overlap with Amplify is simplified."],
    ),
)

_AWS_BEDROCK = AwsServicePricingModel(
    cloud="aws",
    service="Bedrock",
    component_types=["ai_provider"],
    catalog_service_name="Bedrock",
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
        warnings=["Model-specific pricing tiers and provisioned throughput are simplified."],
    ),
)

_AWS_ELASTICACHE = AwsServicePricingModel(
    cloud="aws",
    service="ElastiCache",
    component_types=["cache"],
    catalog_service_name="ElastiCache",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="node_type",
                description="Cache node instance type.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="cache.t3.micro",
            ),
            UsageInputDefinition(
                key="hours_per_month",
                description="Billable node hours while cache cluster is online.",
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
                description="Billable cache node hours.",
                unit="hours/month",
                input_keys=["hours_per_month", "node_type"],
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
        default_values={"node_type": "cache.t3.micro", "hours_per_month": 730, "data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="node-hours",
        billing_granularity="per hour",
        warnings=["Cluster mode and replica nodes multiply node-hour charges."],
    ),
)

_AWS_OPENSEARCH = AwsServicePricingModel(
    cloud="aws",
    service="OpenSearch Service",
    component_types=["search"],
    catalog_service_name="OpenSearch Service",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="instance_hours_per_month",
                description="Search instance hours provisioned per month.",
                unit="hours/month",
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
                description="Outbound transfer from search domain.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="instance_hours",
                description="Billable search instance hours.",
                unit="hours/month",
                input_keys=["instance_hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from instance_hours_per_month.",
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
        default_values={"instance_hours_per_month": 730, "data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="instance-hours and GB-months",
        billing_granularity="per hour; per GB-month",
        warnings=["UltraWarm, cold storage, and dedicated masters are not modeled."],
    ),
)

_AWS_ATHENA = AwsServicePricingModel(
    cloud="aws",
    service="Athena",
    component_types=["analytics"],
    catalog_service_name="Athena",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="data_scanned_tb_per_month",
                description="Data scanned by Athena queries per month.",
                unit="TB/month",
                data_type=InputDataType.float,
                min_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="data_scanned_tb",
                description="Billable data scanned.",
                unit="TB/month",
                input_keys=["data_scanned_tb_per_month"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from data_scanned_tb_per_month.",
            ),
        ],
        default_values={},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="TB scanned",
        billing_granularity="per TB",
        warnings=["Workgroup spillover and federated queries are simplified."],
    ),
)

_AWS_QUICKSIGHT = AwsServicePricingModel(
    cloud="aws",
    service="QuickSight",
    component_types=["analytics"],
    catalog_service_name="QuickSight",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="reader_seats",
                description="QuickSight reader (viewer) seat count.",
                unit="seats",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="author_seats",
                description="QuickSight author seat count.",
                unit="seats",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="reader_seats",
                description="Billable reader seats.",
                unit="seat-months",
                input_keys=["reader_seats"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from reader_seats.",
            ),
            CalculatedSkuDefinition(
                key="author_seats",
                description="Billable author seats.",
                unit="seat-months",
                input_keys=["author_seats"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from author_seats.",
            ),
        ],
        default_values={"reader_seats": 1, "author_seats": 1},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="seats",
        billing_granularity="per seat per month",
        warnings=["SPICE capacity and Q usage are not modeled separately."],
    ),
)

_AWS_SES = AwsServicePricingModel(
    cloud="aws",
    service="SES",
    component_types=["notification"],
    catalog_service_name="SES",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="emails_per_month",
                description="Outbound emails sent per month.",
                unit="emails/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Email payload and attachment egress.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable email send operations.",
                unit="emails/month",
                input_keys=["emails_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from emails_per_month.",
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
            allowances={"requests": 3_000},
            notes="AWS Free Tier: 3,000 outbound emails per month (when eligible).",
        ),
        billing_unit="emails",
        billing_granularity="per 1,000 emails",
        warnings=["Dedicated IP and attachment tiers are simplified."],
    ),
)

_AWS_CLOUDWATCH = AwsServicePricingModel(
    cloud="aws",
    service="CloudWatch",
    component_types=["monitoring"],
    catalog_service_name="CloudWatch",
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
                description="CloudWatch API requests (GetMetricData, PutMetricData, etc.).",
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
        ],
        default_values={"custom_metrics_count": 0, "api_requests_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"custom_metrics": 10, "requests": 1_000_000},
            notes="AWS Free Tier: 10 custom metrics and 1M API requests per month.",
        ),
        billing_unit="metrics and API requests",
        billing_granularity="per metric; per million API requests",
        warnings=["Composite metrics and anomaly detection are not modeled."],
    ),
)

_AWS_CLOUDWATCH_LOGS = AwsServicePricingModel(
    cloud="aws",
    service="CloudWatch Logs",
    component_types=["logging"],
    catalog_service_name="CloudWatch Logs",
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
            allowances={"ingestion_gb": 5, "storage_gb_month": 5},
            notes="AWS Free Tier: 5 GB ingestion and 5 GB storage (simplified).",
        ),
        billing_unit="GB ingestion and GB-months storage",
        billing_granularity="per GB",
        warnings=["Logs Insights query charges are not modeled."],
    ),
)

_AWS_CLOUDWATCH_DASHBOARDS = AwsServicePricingModel(
    cloud="aws",
    service="CloudWatch Dashboards",
    component_types=["analytics"],
    catalog_service_name="CloudWatch Dashboards",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="dashboard_hours_per_month",
                description="Dashboard-hours billed per month (dashboards × hours).",
                unit="dashboard-hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=730,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="dashboard_hours",
                description="Billable dashboard-hours.",
                unit="dashboard-hours/month",
                input_keys=["dashboard_hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from dashboard_hours_per_month.",
            ),
        ],
        default_values={"dashboard_hours_per_month": 730},
        free_tier=FreeTierAllowance(
            allowances={"dashboard_hours": 730},
            notes="AWS Free Tier: 3 dashboards (simplified as 730 dashboard-hours).",
        ),
        billing_unit="dashboard-hours",
        billing_granularity="per dashboard per month",
        warnings=["Metrics displayed on dashboards are billed separately via CloudWatch."],
    ),
)

_AWS_CLOUDWATCH_ALARMS = AwsServicePricingModel(
    cloud="aws",
    service="CloudWatch Alarms",
    component_types=["alerting"],
    catalog_service_name="CloudWatch Alarms",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="standard_alarms_count",
                description="Number of standard CloudWatch alarms provisioned.",
                unit="alarms",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="alarm_evaluations_per_month",
                description="Alarm metric evaluation datapoints per month.",
                unit="evaluations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="alarms",
                description="Billable standard alarm-months.",
                unit="alarm-months",
                input_keys=["standard_alarms_count"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from standard_alarms_count.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable alarm evaluations.",
                unit="evaluations/month",
                input_keys=["alarm_evaluations_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from alarm_evaluations_per_month.",
            ),
        ],
        default_values={"standard_alarms_count": 1, "alarm_evaluations_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"alarms": 10},
            notes="AWS Free Tier: 10 standard alarms (simplified).",
        ),
        billing_unit="alarms and evaluations",
        billing_granularity="per alarm per month",
        warnings=["Composite and anomaly alarms use different meters."],
    ),
)

_AWS_SSM = AwsServicePricingModel(
    cloud="aws",
    service="SSM Parameter Store",
    component_types=["config", "secrets"],
    catalog_service_name="SSM Parameter Store",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="parameters_count",
                description="Standard parameters stored during the month.",
                unit="parameters",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="api_calls_per_month",
                description="GetParameter and related API calls.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="parameter_months",
                description="Billable parameter-months.",
                unit="parameter-months",
                input_keys=["parameters_count"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from parameters_count.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable Parameter Store API calls.",
                unit="operations/month",
                input_keys=["api_calls_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from api_calls_per_month.",
            ),
        ],
        default_values={"parameters_count": 1, "api_calls_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"parameter_months": 10_000, "requests": 1_000_000},
            notes="AWS Free Tier: 10K standard parameters and 1M API calls (simplified).",
        ),
        billing_unit="parameters and API calls",
        billing_granularity="per parameter per month; per 10K API calls",
        warnings=["Advanced parameters and throughput tiers are not modeled."],
    ),
)

_AWS_APPCONFIG = AwsServicePricingModel(
    cloud="aws",
    service="AppConfig",
    component_types=["config"],
    catalog_service_name="AppConfig",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="configurations_count",
                description="Configuration profiles stored during the month.",
                unit="configurations",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="deployment_events_per_month",
                description="Configuration deployment events per month.",
                unit="events/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="configuration_months",
                description="Billable configuration-months.",
                unit="configuration-months",
                input_keys=["configurations_count"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from configurations_count.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable deployment events.",
                unit="events/month",
                input_keys=["deployment_events_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from deployment_events_per_month.",
            ),
        ],
        default_values={"configurations_count": 1, "deployment_events_per_month": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="configurations and deployment events",
        billing_granularity="per configuration per month; per event",
        warnings=["Hosted configuration versions share meters with SSM in some setups."],
    ),
)

_AWS_XRAY = AwsServicePricingModel(
    cloud="aws",
    service="X-Ray",
    component_types=["tracing"],
    catalog_service_name="X-Ray",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="traces_ingested_per_month",
                description="Traces recorded and stored per month.",
                unit="traces/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="traces_scanned_per_month",
                description="Traces retrieved or scanned via API per month.",
                unit="traces/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="traces_ingested",
                description="Billable traces ingested.",
                unit="traces/month",
                input_keys=["traces_ingested_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from traces_ingested_per_month.",
            ),
            CalculatedSkuDefinition(
                key="traces_scanned",
                description="Billable traces scanned.",
                unit="traces/month",
                input_keys=["traces_scanned_per_month"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from traces_scanned_per_month.",
            ),
        ],
        default_values={"traces_scanned_per_month": 0},
        free_tier=FreeTierAllowance(
            allowances={"traces_ingested": 100_000},
            notes="AWS Free Tier: 100K traces recorded per month (simplified).",
        ),
        billing_unit="traces",
        billing_granularity="per million traces",
        warnings=["Sampling rules and Insights queries are simplified."],
    ),
)

EXTENDED_AWS_PRICING_MODELS: tuple[AwsServicePricingModel, ...] = (
    _AWS_AMPLIFY,
    _AWS_AMPLIFY_HOSTING,
    _AWS_BEDROCK,
    _AWS_ELASTICACHE,
    _AWS_OPENSEARCH,
    _AWS_ATHENA,
    _AWS_QUICKSIGHT,
    _AWS_SES,
    _AWS_CLOUDWATCH,
    _AWS_CLOUDWATCH_LOGS,
    _AWS_CLOUDWATCH_DASHBOARDS,
    _AWS_CLOUDWATCH_ALARMS,
    _AWS_SSM,
    _AWS_APPCONFIG,
    _AWS_XRAY,
)
