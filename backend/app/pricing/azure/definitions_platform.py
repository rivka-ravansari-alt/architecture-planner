"""Azure pricing models for platform edge services (API Management, CDN, load balancing)."""

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

_AZURE_API_MANAGEMENT = AzureServicePricingModel(
    cloud="azure",
    service="API Management",
    component_types=["api_gateway"],
    catalog_service_name="API Management",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="requests_per_month",
                description="API gateway requests handled per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Response payload egress through API Management.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="sku_tier",
                description="Consumption, Developer, Basic, Standard, or Premium tier.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Consumption",
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable API requests.",
                unit="requests/month",
                input_keys=["requests_per_month", "sku_tier"],
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
        default_values={"data_egress_gb": 0, "sku_tier": "Consumption"},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="requests",
        billing_granularity="per million requests on consumption tier",
        warnings=["Dedicated gateway units and VNet integration are simplified."],
    ),
)

_AZURE_APPLICATION_GATEWAY = AzureServicePricingModel(
    cloud="azure",
    service="Application Gateway",
    component_types=["load_balancer"],
    catalog_service_name="Application Gateway",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="hours_per_month",
                description="Hours the application gateway is provisioned.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
            UsageInputDefinition(
                key="capacity_unit_hours",
                description="Application Gateway Capacity Unit-hours consumed.",
                unit="CU-hours/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer through the gateway.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="gateway_hours",
                description="Billable gateway provisioned hours.",
                unit="hours/month",
                input_keys=["hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from hours_per_month.",
            ),
            CalculatedSkuDefinition(
                key="capacity_unit_hours",
                description="Billable capacity unit-hours.",
                unit="CU-hours/month",
                input_keys=["capacity_unit_hours"],
                catalog_sku_roles=["memory"],
                derivation="Direct mapping from capacity_unit_hours.",
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
        default_values={"hours_per_month": 730, "capacity_unit_hours": 0, "data_egress_gb": 0},
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="gateway hours and capacity units",
        billing_granularity="per hour; per capacity unit-hour",
        warnings=["WAF and SSL policies are not modeled separately."],
    ),
)

_AZURE_CDN = AzureServicePricingModel(
    cloud="azure",
    service="Content Delivery Network",
    component_types=["cdn"],
    catalog_service_name="Content Delivery Network",
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
        free_tier=_FREE_TIER_EMPTY,
        billing_unit="requests and GB transfer",
        billing_granularity="per 10K requests; per GB egress",
        warnings=["Regional price tiers and origin shield are simplified."],
    ),
)

PLATFORM_AZURE_PRICING_MODELS: tuple[AzureServicePricingModel, ...] = (
    _AZURE_API_MANAGEMENT,
    _AZURE_APPLICATION_GATEWAY,
    _AZURE_CDN,
)
