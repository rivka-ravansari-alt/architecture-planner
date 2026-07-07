"""Dispatch GCP SKU quantity calculators by service."""

from __future__ import annotations

from app.pricing.gcp.sku_quantities.api_gateway import calculate_api_gateway_quantities
from app.pricing.gcp.sku_quantities.cloud_firestore import calculate_cloud_firestore_quantities
from app.pricing.gcp.sku_quantities.cloud_memorystore import calculate_cloud_memorystore_quantities
from app.pricing.gcp.sku_quantities.cloud_pubsub import calculate_cloud_pubsub_quantities
from app.pricing.gcp.sku_quantities.cloud_run import calculate_cloud_run_quantities
from app.pricing.gcp.sku_quantities.cloud_run_functions import calculate_cloud_run_functions_quantities
from app.pricing.gcp.sku_quantities.cloud_sql import calculate_cloud_sql_quantities
from app.pricing.gcp.sku_quantities.cloud_storage import calculate_cloud_storage_quantities
from app.pricing.gcp.sku_quantities.cloud_tasks import calculate_cloud_tasks_quantities
from app.pricing.gcp.sku_quantities.extended import EXTENDED_GCP_SKU_CALCULATORS
from app.pricing.gcp.sku_quantities.networking import calculate_networking_quantities
from app.pricing.gcp.sku_quantities.secret_manager import calculate_secret_manager_quantities
from app.pricing.schemas import GcpServicePricingModel, SkuQuantityResult, UsageAssumption

_CALCULATORS = {
    "Cloud Run Functions": calculate_cloud_run_functions_quantities,
    "Cloud Run": calculate_cloud_run_quantities,
    "Cloud SQL": calculate_cloud_sql_quantities,
    "Cloud Firestore": calculate_cloud_firestore_quantities,
    "Cloud Storage": calculate_cloud_storage_quantities,
    "Cloud Pub/Sub": calculate_cloud_pubsub_quantities,
    "Cloud Tasks": calculate_cloud_tasks_quantities,
    "Cloud Memorystore for Redis": calculate_cloud_memorystore_quantities,
    "API Gateway": calculate_api_gateway_quantities,
    "Secret Manager": calculate_secret_manager_quantities,
    "Networking": calculate_networking_quantities,
    **EXTENDED_GCP_SKU_CALCULATORS,
}


def calculate_gcp_sku_quantities(
    model: GcpServicePricingModel,
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
