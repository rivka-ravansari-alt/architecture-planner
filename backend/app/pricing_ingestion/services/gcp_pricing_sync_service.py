"""Orchestrates GCP catalog pricing sync into Firestore."""

from __future__ import annotations

import logging
import time

from app.config.params import (
    PRICE_IMPORT_STATUS_COMPLETED,
    PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS,
    PRICE_IMPORT_STATUS_FAILED,
    PRICING_PROVIDER_GCP,
)
from app.pricing_ingestion.clients.gcp_billing_client import GcpBillingClient
from app.pricing_ingestion.models.documents import ImportRunError
from app.pricing_ingestion.normalizers.gcp_catalog_normalizer import GcpCatalogNormalizer
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.schemas.sync import ProviderPricingSyncResponse
from app.pricing_ingestion.services.base_pricing_sync_service import BasePricingSyncService
from app.pricing_ingestion.services.firestore_gcp_catalog_loader import FirestoreGcpCatalogLoader
from app.pricing_ingestion.services.gcp_billing_service_resolver import GcpBillingServiceResolver

logger = logging.getLogger(__name__)

_SERVICE_FETCH_DELAY_SECONDS = 0.25


class GcpPricingSyncService(BasePricingSyncService):
    provider = PRICING_PROVIDER_GCP

    def __init__(
        self,
        *,
        billing_client: GcpBillingClient,
        catalog_repo: GcpCatalogRepository,
        import_runs_repo: PriceImportRunsRepository,
        service_loader: FirestoreGcpCatalogLoader,
        normalizer: GcpCatalogNormalizer | None = None,
    ) -> None:
        super().__init__(import_runs_repo=import_runs_repo)
        self._billing_client = billing_client
        self._catalog_repo = catalog_repo
        self._service_loader = service_loader
        self._normalizer = normalizer or GcpCatalogNormalizer()

    def sync(self, *, triggered_by: str | None = None) -> ProviderPricingSyncResponse:
        import_run = self._start_run(triggered_by=triggered_by)

        service_names = self._service_loader.list_enabled_service_names()
        if not service_names:
            return self._finalize_run(
                import_run,
                status=PRICE_IMPORT_STATUS_FAILED,
                services_total=0,
                services_succeeded=0,
                services_failed=0,
                skus_upserted=0,
                errors=[
                    ImportRunError(
                        service_id="",
                        message="No enabled GCP service names found in Firestore gcp_catalog.",
                    )
                ],
            )

        try:
            billing_services = self._billing_client.list_services()
        except Exception as exc:
            logger.exception(
                "gcp_catalog_import run_id=%s failed to list billing services",
                import_run.id,
            )
            return self._finalize_run(
                import_run,
                status=PRICE_IMPORT_STATUS_FAILED,
                services_total=len(service_names),
                services_succeeded=0,
                services_failed=len(service_names),
                skus_upserted=0,
                errors=[ImportRunError(service_id="", message=str(exc))],
            )

        resolver = GcpBillingServiceResolver(billing_services)
        errors: list[ImportRunError] = []
        services_succeeded = 0
        services_failed = 0
        skus_upserted = 0

        for service_name in service_names:
            try:
                service = resolver.resolve(service_name)
                if service is None:
                    raise ValueError(
                        f"No GCP billing catalog match for service name '{service_name}'"
                    )

                service_id = str(service.get("serviceId", ""))
                skus = self._billing_client.list_skus_for_service(service_id)
                record = self._normalizer.normalize_service(service=service, skus=skus)
                if record is None:
                    raise ValueError(f"No priced SKUs found for service '{service_name}'")

                self._catalog_repo.upsert(record)
                skus_upserted += record.sku_count
                services_succeeded += 1
                logger.info(
                    "gcp_catalog_import run_id=%s service=%s id=%s skus=%s status=ok",
                    import_run.id,
                    record.name,
                    record.id,
                    record.sku_count,
                )
            except Exception as exc:
                services_failed += 1
                errors.append(ImportRunError(service_id=service_name, message=str(exc)))
                logger.exception(
                    "gcp_catalog_import run_id=%s service=%s status=failed",
                    import_run.id,
                    service_name,
                )

            time.sleep(_SERVICE_FETCH_DELAY_SECONDS)

        status = PRICE_IMPORT_STATUS_COMPLETED
        if services_failed and services_succeeded:
            status = PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
        elif services_failed and not services_succeeded:
            status = PRICE_IMPORT_STATUS_FAILED

        return self._finalize_run(
            import_run,
            status=status,
            services_total=len(service_names),
            services_succeeded=services_succeeded,
            services_failed=services_failed,
            skus_upserted=skus_upserted,
            errors=errors,
        )
