"""Admin pricing ingestion HTTP controller."""

from __future__ import annotations

from app.pricing_ingestion.schemas.sync import (
    CombinedPricingSyncResponse,
    PricingSyncRequest,
    ProviderPricingSyncResponse,
)
from app.pricing_ingestion.services.pricing_sync_orchestrator import PricingSyncOrchestrator


class AdminPricingController:
    def __init__(self, orchestrator: PricingSyncOrchestrator) -> None:
        self._orchestrator = orchestrator

    def sync_pricing(
        self,
        request: PricingSyncRequest,
        *,
        triggered_by: str | None = None,
    ) -> ProviderPricingSyncResponse | CombinedPricingSyncResponse:
        return self._orchestrator.sync(request, triggered_by=triggered_by)
