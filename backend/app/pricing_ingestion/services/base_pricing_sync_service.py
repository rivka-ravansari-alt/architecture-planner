"""Shared pricing sync run lifecycle helpers."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from app.config.params import PRICE_IMPORT_STATUS_RUNNING
from app.pricing_ingestion.models.documents import ImportRunError, PriceImportRunRecord
from app.pricing_ingestion.providers.base import PricingSyncService
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.schemas.sync import ImportRunErrorOut, ProviderPricingSyncResponse

logger = logging.getLogger(__name__)


class BasePricingSyncService(PricingSyncService):
    """Base class with shared import-run tracking in Firestore."""

    def __init__(self, *, import_runs_repo: PriceImportRunsRepository) -> None:
        self._import_runs_repo = import_runs_repo

    def _start_run(self, *, triggered_by: str | None) -> PriceImportRunRecord:
        run_id = str(uuid.uuid4())
        import_run = PriceImportRunRecord(
            id=run_id,
            provider=self.provider,
            status=PRICE_IMPORT_STATUS_RUNNING,
            started_at=datetime.now(UTC),
            triggered_by=triggered_by,
        )
        self._import_runs_repo.create(import_run)
        logger.info("%s_catalog_import run_id=%s status=started", self.provider, run_id)
        return import_run

    def _finalize_run(
        self,
        import_run: PriceImportRunRecord,
        *,
        status: str,
        services_total: int,
        services_succeeded: int,
        services_failed: int,
        skus_upserted: int,
        errors: list[ImportRunError],
    ) -> ProviderPricingSyncResponse:
        ended_at = datetime.now(UTC)
        import_run.status = status
        import_run.ended_at = ended_at
        import_run.services_total = services_total
        import_run.services_succeeded = services_succeeded
        import_run.services_failed = services_failed
        import_run.skus_upserted = skus_upserted
        import_run.errors = errors
        self._import_runs_repo.update(import_run)

        logger.info(
            "%s_catalog_import run_id=%s status=%s services_total=%s skus_upserted=%s",
            self.provider,
            import_run.id,
            status,
            services_total,
            skus_upserted,
        )

        return ProviderPricingSyncResponse(
            provider=self.provider,
            import_run_id=import_run.id,
            status=status,
            started_at=import_run.started_at,
            ended_at=ended_at,
            services_total=services_total,
            services_succeeded=services_succeeded,
            services_failed=services_failed,
            skus_upserted=skus_upserted,
            errors=[
                ImportRunErrorOut(service_id=error.service_id, message=error.message)
                for error in errors
            ],
        )
