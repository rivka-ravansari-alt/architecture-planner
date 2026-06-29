"""Factory helpers for pricing sync services (HTTP and job entrypoints)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.params import (
    PRICING_PROVIDER_AWS,
    PRICING_PROVIDER_AZURE,
    PRICING_PROVIDER_GCP,
)
from app.pricing_ingestion.clients.aws_billing_client import AwsBillingClient
from app.pricing_ingestion.clients.azure_billing_client import AzureBillingClient
from app.pricing_ingestion.clients.gcp_billing_client import GcpBillingClient
from app.pricing_ingestion.providers.registry import PricingSyncRegistry
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.services.aws_pricing_sync_service import AwsPricingSyncService
from app.pricing_ingestion.services.azure_pricing_sync_service import AzurePricingSyncService
from app.pricing_ingestion.services.db_aws_catalog_loader import DbAwsCatalogLoader
from app.pricing_ingestion.services.db_azure_catalog_loader import DbAzureCatalogLoader
from app.pricing_ingestion.services.firestore_gcp_catalog_loader import FirestoreGcpCatalogLoader
from app.pricing_ingestion.services.gcp_pricing_sync_service import GcpPricingSyncService
from app.pricing_ingestion.services.pricing_sync_orchestrator import PricingSyncOrchestrator
from app.repositories.component_catalog_repository import ComponentCatalogRepository


def build_pricing_sync_registry(db: Session) -> PricingSyncRegistry:
    firestore_client = FirestoreClientFactory.create()
    import_runs_repo = PriceImportRunsRepository(firestore_client)
    gcp_catalog_repo = GcpCatalogRepository(firestore_client)
    azure_catalog_repo = AzureCatalogRepository(firestore_client)
    component_catalog_repo = ComponentCatalogRepository(db)

    return PricingSyncRegistry(
        {
            PRICING_PROVIDER_GCP: GcpPricingSyncService(
                billing_client=GcpBillingClient(),
                catalog_repo=gcp_catalog_repo,
                import_runs_repo=import_runs_repo,
                service_loader=FirestoreGcpCatalogLoader(gcp_catalog_repo),
            ),
            PRICING_PROVIDER_AWS: AwsPricingSyncService(
                billing_client=AwsBillingClient(),
                catalog_repo=AwsCatalogRepository(firestore_client),
                import_runs_repo=import_runs_repo,
                service_loader=DbAwsCatalogLoader(component_catalog_repo),
            ),
            PRICING_PROVIDER_AZURE: AzurePricingSyncService(
                billing_client=AzureBillingClient(),
                catalog_repo=azure_catalog_repo,
                import_runs_repo=import_runs_repo,
                service_loader=DbAzureCatalogLoader(component_catalog_repo),
            ),
        }
    )


def build_pricing_sync_orchestrator(db: Session) -> PricingSyncOrchestrator:
    return PricingSyncOrchestrator(build_pricing_sync_registry(db))
