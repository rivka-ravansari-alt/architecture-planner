"""Dispatch Azure SKU quantity calculators by service."""

from __future__ import annotations

from app.pricing.azure.sku_quantities.blob_storage import calculate_blob_storage_quantities
from app.pricing.azure.sku_quantities.container_apps import calculate_container_apps_quantities
from app.pricing.azure.sku_quantities.extended import EXTENDED_AZURE_SKU_CALCULATORS
from app.pricing.azure.sku_quantities.functions import calculate_functions_quantities
from app.pricing.azure.sku_quantities.platform import PLATFORM_AZURE_SKU_CALCULATORS
from app.pricing.azure.sku_quantities.queue_storage import calculate_queue_storage_quantities
from app.pricing.azure.sku_quantities.service_bus import calculate_service_bus_quantities
from app.pricing.azure.sku_quantities.sql_database import calculate_sql_database_quantities
from app.pricing.schemas import AzureServicePricingModel, SkuQuantityResult, UsageAssumption

_CALCULATORS = {
    "Azure Container Apps": calculate_container_apps_quantities,
    "Azure Functions": calculate_functions_quantities,
    "Azure Blob Storage": calculate_blob_storage_quantities,
    "Azure SQL Database": calculate_sql_database_quantities,
    "Azure Queue Storage": calculate_queue_storage_quantities,
    "Azure Service Bus": calculate_service_bus_quantities,
    **PLATFORM_AZURE_SKU_CALCULATORS,
    **EXTENDED_AZURE_SKU_CALCULATORS,
}


def calculate_azure_sku_quantities(
    model: AzureServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    """Convert resolved usage assumptions into deterministic SKU quantities."""
    calculator = _CALCULATORS.get(model.service)
    if calculator is None:
        return SkuQuantityResult(
            service=model.service,
            quantities=[],
            missing=[],
            ready=False,
        )
    return calculator(model, resolved)
