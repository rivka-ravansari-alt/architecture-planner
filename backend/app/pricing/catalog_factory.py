"""Build pricing pipelines backed by Firestore catalog data.

All runtime pricing (web app, benchmarks, validation scripts) must use these
factories so catalog unit prices come from a single source of truth.
"""

from __future__ import annotations

from typing import Any

from app.pricing.aws.catalog_lookup import AwsCatalogLookup
from app.pricing.aws.cost_calculator import AwsCostCalculator
from app.pricing.aws.meter_scaling import AwsMeterUnitScaler
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.aws.sku_roles import AwsSkuRoleResolver
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.pricing.azure.catalog_lookup import AzureCatalogLookup
from app.pricing.azure.catalog_meter_selector import AzureCatalogMeterSelector
from app.pricing.azure.cost_calculator import AzureCostCalculator
from app.pricing.azure.meter_scaling import MeterUnitScaler
from app.pricing.azure.project_costing import AzureProjectCostingPipeline
from app.pricing.azure.sku_roles import SkuRoleResolver
from app.pricing.azure.usage_inference import AzureUsageInferenceEngine
from app.pricing.gcp.catalog_lookup import GcpCatalogLookup
from app.pricing.gcp.catalog_meter_selector import GcpCatalogMeterSelector
from app.pricing.gcp.cost_calculator import GcpCostCalculator
from app.pricing.gcp.meter_scaling import GcpMeterUnitScaler
from app.pricing.gcp.project_costing import GcpProjectCostingPipeline
from app.pricing.gcp.sku_roles import GcpSkuRoleResolver
from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine
from app.pricing.providers.heuristic import HeuristicProviderPricing
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.services.component_mapper_service import ComponentMapperService
from app.services.project_pricing_service import ProjectPricingService


def create_firestore_client(client: Any | None = None) -> Any:
    """Return a shared Firestore client (creates one when omitted)."""
    return client if client is not None else FirestoreClientFactory.create()


def build_aws_cost_calculator(*, firestore_client: Any | None = None) -> AwsCostCalculator:
    """AWS cost calculator reading unit prices from Firestore aws_catalog."""
    client = create_firestore_client(firestore_client)
    lookup = AwsCatalogLookup(AwsCatalogRepository(client))
    return AwsCostCalculator(lookup, AwsSkuRoleResolver(), AwsMeterUnitScaler())


def build_azure_cost_calculator(*, firestore_client: Any | None = None) -> AzureCostCalculator:
    """Azure cost calculator reading unit prices from Firestore azure_catalog."""
    client = create_firestore_client(firestore_client)
    lookup = AzureCatalogLookup(
        AzureCatalogRepository(client),
        meter_selector=AzureCatalogMeterSelector(),
    )
    return AzureCostCalculator(lookup, SkuRoleResolver(), MeterUnitScaler())


def build_gcp_cost_calculator(*, firestore_client: Any | None = None) -> GcpCostCalculator:
    """GCP cost calculator reading unit prices from Firestore gcp_catalog."""
    client = create_firestore_client(firestore_client)
    lookup = GcpCatalogLookup(
        GcpCatalogRepository(client),
        meter_selector=GcpCatalogMeterSelector(),
    )
    return GcpCostCalculator(lookup, GcpSkuRoleResolver(), GcpMeterUnitScaler())


def build_aws_project_costing_pipeline(
    *,
    firestore_client: Any | None = None,
) -> AwsProjectCostingPipeline:
    return AwsProjectCostingPipeline(
        AwsUsageInferenceEngine(),
        build_aws_cost_calculator(firestore_client=firestore_client),
    )


def build_azure_project_costing_pipeline(
    *,
    firestore_client: Any | None = None,
) -> AzureProjectCostingPipeline:
    return AzureProjectCostingPipeline(
        AzureUsageInferenceEngine(),
        build_azure_cost_calculator(firestore_client=firestore_client),
    )


def build_gcp_project_costing_pipeline(
    *,
    firestore_client: Any | None = None,
) -> GcpProjectCostingPipeline:
    return GcpProjectCostingPipeline(
        GcpUsageInferenceEngine(),
        build_gcp_cost_calculator(firestore_client=firestore_client),
    )


def build_project_pricing_service(
    mapper: ComponentMapperService,
    *,
    firestore_client: Any | None = None,
) -> ProjectPricingService:
    """Full multi-provider pricing service using Firestore catalogs."""
    client = create_firestore_client(firestore_client)
    return ProjectPricingService(
        build_azure_project_costing_pipeline(firestore_client=client),
        build_aws_project_costing_pipeline(firestore_client=client),
        build_gcp_project_costing_pipeline(firestore_client=client),
        HeuristicProviderPricing(mapper=mapper),
    )
