"""Orchestrates AWS catalog pricing sync into Firestore."""

from __future__ import annotations

import logging
import time

from app.config.params import (
    PRICE_IMPORT_STATUS_COMPLETED,
    PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS,
    PRICE_IMPORT_STATUS_FAILED,
    PRICING_PROVIDER_AWS,
)
from app.pricing_ingestion.clients.aws_billing_client import AwsBillingClient
from app.pricing_ingestion.models.documents import ImportRunError
from app.pricing_ingestion.normalizers.aws_catalog_normalizer import AwsCatalogNormalizer
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.schemas.sync import ProviderPricingSyncResponse
from app.pricing_ingestion.services.aws_billing_service_resolver import AwsBillingServiceResolver
from app.pricing_ingestion.services.base_pricing_sync_service import BasePricingSyncService
from app.pricing_ingestion.services.db_aws_catalog_loader import DbAwsCatalogLoader

logger = logging.getLogger(__name__)

_SERVICE_FETCH_DELAY_SECONDS = 0.25


class AwsPricingSyncService(BasePricingSyncService):
    provider = PRICING_PROVIDER_AWS

    def __init__(
        self,
        *,
        billing_client: AwsBillingClient,
        catalog_repo: AwsCatalogRepository,
        import_runs_repo: PriceImportRunsRepository,
        service_loader: DbAwsCatalogLoader,
        normalizer: AwsCatalogNormalizer | None = None,
    ) -> None:
        super().__init__(import_runs_repo=import_runs_repo)
        self._billing_client = billing_client
        self._catalog_repo = catalog_repo
        self._service_loader = service_loader
        self._normalizer = normalizer or AwsCatalogNormalizer()

    def sync(self, *, triggered_by: str | None = None) -> ProviderPricingSyncResponse:
        import_run = self._start_run(triggered_by=triggered_by)

        catalog_services = self._service_loader.list_enabled_services()
        if not catalog_services:
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
                        message="No AWS service names found in the component catalog database.",
                    )
                ],
            )

        try:
            billing_services = self._billing_client.list_services(catalog_services)
        except Exception as exc:
            logger.exception(
                "aws_catalog_import run_id=%s failed to list billing services",
                import_run.id,
            )
            return self._finalize_run(
                import_run,
                status=PRICE_IMPORT_STATUS_FAILED,
                services_total=len(catalog_services),
                services_succeeded=0,
                services_failed=len(catalog_services),
                skus_upserted=0,
                errors=[ImportRunError(service_id="", message=str(exc))],
            )

        resolver = AwsBillingServiceResolver(billing_services)
        errors: list[ImportRunError] = []
        services_succeeded = 0
        services_failed = 0
        skus_upserted = 0

        for catalog_service in catalog_services:
            try:
                service = resolver.resolve(catalog_service)
                if service is None:
                    raise ValueError(
                        f"No AWS billing catalog match for service name '{catalog_service.name}'"
                    )

                service_id = str(service.get("serviceId", ""))
                skus = self._billing_client.list_skus_for_service(
                    service_id,
                    catalog_service=catalog_service,
                )
                record = self._normalizer.normalize_service(service=service, skus=skus)
                if record is None:
                    raise ValueError(f"No priced SKUs found for service '{catalog_service.name}'")

                self._catalog_repo.upsert(record)
                skus_upserted += record.sku_count
                services_succeeded += 1
                logger.info(
                    "aws_catalog_import run_id=%s service=%s id=%s skus=%s status=ok",
                    import_run.id,
                    record.name,
                    record.id,
                    record.sku_count,
                )
            except Exception as exc:
                services_failed += 1
                errors.append(ImportRunError(service_id=catalog_service.name, message=str(exc)))
                logger.exception(
                    "aws_catalog_import run_id=%s service=%s status=failed",
                    import_run.id,
                    catalog_service.name,
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
            services_total=len(catalog_services),
            services_succeeded=services_succeeded,
            services_failed=services_failed,
            skus_upserted=skus_upserted,
            errors=errors,
        )
