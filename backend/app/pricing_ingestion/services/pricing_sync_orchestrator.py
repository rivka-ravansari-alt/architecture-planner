"""Multi-provider pricing sync orchestration."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config.params import (
    PRICE_IMPORT_STATUS_COMPLETED,
    PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS,
    PRICE_IMPORT_STATUS_FAILED,
    PRICING_PROVIDER_ALL,
)
from app.pricing_ingestion.providers.registry import PricingSyncRegistry
from app.pricing_ingestion.schemas.sync import (
    CombinedPricingSyncResponse,
    PricingSyncRequest,
    ProviderPricingSyncResponse,
)


class PricingSyncOrchestrator:
    def __init__(self, registry: PricingSyncRegistry) -> None:
        self._registry = registry

    def sync(
        self,
        request: PricingSyncRequest,
        *,
        triggered_by: str | None = None,
    ) -> ProviderPricingSyncResponse | CombinedPricingSyncResponse:
        if request.provider == PRICING_PROVIDER_ALL:
            return self._sync_all(triggered_by=triggered_by)
        return self._registry.get(request.provider).sync(triggered_by=triggered_by)

    def _sync_all(self, *, triggered_by: str | None) -> CombinedPricingSyncResponse:
        started_at = datetime.now(UTC)
        results: list[ProviderPricingSyncResponse] = []

        for service in self._registry.all():
            results.append(service.sync(triggered_by=triggered_by))

        ended_at = datetime.now(UTC)
        services_total = sum(result.services_total for result in results)
        services_succeeded = sum(result.services_succeeded for result in results)
        services_failed = sum(result.services_failed for result in results)
        skus_upserted = sum(result.skus_upserted for result in results)

        statuses = {result.status for result in results}
        if statuses == {PRICE_IMPORT_STATUS_COMPLETED}:
            status = PRICE_IMPORT_STATUS_COMPLETED
        elif statuses == {PRICE_IMPORT_STATUS_FAILED}:
            status = PRICE_IMPORT_STATUS_FAILED
        else:
            status = PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS

        return CombinedPricingSyncResponse(
            provider=PRICING_PROVIDER_ALL,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            services_total=services_total,
            services_succeeded=services_succeeded,
            services_failed=services_failed,
            skus_upserted=skus_upserted,
            providers=results,
        )
