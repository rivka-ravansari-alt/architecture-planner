"""SKU quantity calculators for Azure platform edge services."""

from __future__ import annotations

from app.pricing.azure.sku_quantities._helpers import (
    assumptions_by_key,
    collect_missing_required,
    make_quantity,
    numeric_value,
    optional_numeric,
)
from app.pricing.schemas import AzureServicePricingModel, SkuQuantity, SkuQuantityResult, UsageAssumption


def calculate_api_management_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["requests_per_month"]
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    assumption_map = assumptions_by_key(resolved)
    requests = numeric_value(assumption_map, "requests_per_month")
    egress = optional_numeric(assumption_map, "data_egress_gb", 0)
    quantities: list[SkuQuantity] = [
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month", "sku_tier"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(egress),
            unit="GB/month",
            formula="data_egress_gb",
            assumption_map=assumption_map,
            input_keys=["data_egress_gb"],
        ),
    ]
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)


def calculate_application_gateway_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required: list[str] = []
    assumption_map = assumptions_by_key(resolved)
    hours = optional_numeric(assumption_map, "hours_per_month", 730)
    cu_hours = optional_numeric(assumption_map, "capacity_unit_hours", 0)
    egress = optional_numeric(assumption_map, "data_egress_gb", 0)
    quantities = [
        make_quantity(
            sku_key="gateway_hours",
            quantity=float(hours),
            unit="hours/month",
            formula="hours_per_month",
            assumption_map=assumption_map,
            input_keys=["hours_per_month"],
        ),
        make_quantity(
            sku_key="capacity_unit_hours",
            quantity=float(cu_hours),
            unit="CU-hours/month",
            formula="capacity_unit_hours",
            assumption_map=assumption_map,
            input_keys=["capacity_unit_hours"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(egress),
            unit="GB/month",
            formula="data_egress_gb",
            assumption_map=assumption_map,
            input_keys=["data_egress_gb"],
        ),
    ]
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)


def calculate_cdn_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    required = ["requests_per_month"]
    missing = collect_missing_required(model, resolved, keys=required)
    if missing:
        return SkuQuantityResult(service=model.service, quantities=[], missing=missing, ready=False)

    assumption_map = assumptions_by_key(resolved)
    requests = numeric_value(assumption_map, "requests_per_month")
    transfer = optional_numeric(assumption_map, "data_transfer_gb", 0)
    quantities = [
        make_quantity(
            sku_key="requests",
            quantity=float(requests),
            unit="requests/month",
            formula="requests_per_month",
            assumption_map=assumption_map,
            input_keys=["requests_per_month"],
        ),
        make_quantity(
            sku_key="egress_gb",
            quantity=float(transfer),
            unit="GB/month",
            formula="data_transfer_gb",
            assumption_map=assumption_map,
            input_keys=["data_transfer_gb"],
        ),
    ]
    return SkuQuantityResult(service=model.service, quantities=quantities, missing=[], ready=True)


PLATFORM_AZURE_SKU_CALCULATORS = {
    "API Management": calculate_api_management_quantities,
    "Application Gateway": calculate_application_gateway_quantities,
    "Content Delivery Network": calculate_cdn_quantities,
}
