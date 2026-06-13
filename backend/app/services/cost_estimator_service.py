"""Deterministic monthly cost estimation from architecture and usage data."""

from __future__ import annotations

from app.config.cost_rules import ROUGH_AI_MONTHLY, ROUGH_EXTERNAL_MONTHLY, STAGE_EXTERNAL_OVERHEAD
from app.config.params import CLOUD_PROVIDERS, COST_CURRENCY
from app.schemas.cost import CostBreakdownOut, CostRange, CostRangeOut, UsageProfile
from app.schemas.domain import MappedComponent
from app.services.cloud_infrastructure_cost_service import CloudInfrastructureCostService
from app.services.cost_estimate_metadata_service import CostEstimateMetadataService


class CostEstimatorService:
    def __init__(
        self,
        metadata: CostEstimateMetadataService | None = None,
        cloud_infrastructure: CloudInfrastructureCostService | None = None,
    ) -> None:
        self._metadata = metadata or CostEstimateMetadataService()
        self._cloud_infrastructure = cloud_infrastructure or CloudInfrastructureCostService()

    def estimate(
        self,
        *,
        components: list[MappedComponent],
        usage: UsageProfile,
    ) -> CostBreakdownOut:
        active_components = [component for component in components if not component.optional]
        cloud_infra = self._cloud_infrastructure.estimate(active_components, usage)
        cloud_cost = dict(cloud_infra.provider_totals)

        ai_services_cost = self._rough_ai_cost(usage)
        external_services_cost = self._rough_external_cost(usage)

        cloud_total = CostRange()
        for provider_range in cloud_cost.values():
            cloud_total.add(provider_range.low, provider_range.high)

        other_total = CostRange()
        for provider_range in ai_services_cost.values():
            other_total.add(provider_range.low, provider_range.high)
        for provider_range in external_services_cost.values():
            other_total.add(provider_range.low, provider_range.high)

        total = CostRange(low=cloud_total.low + other_total.low, high=cloud_total.high + other_total.high)

        return CostBreakdownOut(
            cloud_infrastructure=cloud_infra,
            cloud_cost=cloud_cost,
            ai_services_cost=ai_services_cost,
            external_services_cost=external_services_cost,
            total_monthly_cost=CostRangeOut(**total.round_int().to_dict()),
            assumptions=self._metadata.build_assumptions(usage),
            unknown_items=self._metadata.build_unknown_items(usage, active_components),
            confidence=self._metadata.compute_confidence(usage),
            disclaimer=self._metadata.disclaimer(),
            currency=COST_CURRENCY,
        )

    def _rough_ai_cost(self, usage: UsageProfile) -> dict[str, CostRangeOut]:
        if not usage.ai:
            return {}
        stage_factor = STAGE_EXTERNAL_OVERHEAD.get(usage.stage, 1.0)
        rough = CostRange(low=ROUGH_AI_MONTHLY[0], high=ROUGH_AI_MONTHLY[1]).scale(stage_factor)
        return {"ai_services": CostRangeOut(**rough.round_int().to_dict())}

    def _rough_external_cost(self, usage: UsageProfile) -> dict[str, CostRangeOut]:
        if not (usage.payments or usage.notifications or usage.external_integrations):
            return {}
        stage_factor = STAGE_EXTERNAL_OVERHEAD.get(usage.stage, 1.0)
        rough = CostRange(low=ROUGH_EXTERNAL_MONTHLY[0], high=ROUGH_EXTERNAL_MONTHLY[1]).scale(stage_factor)
        return {"external_services": CostRangeOut(**rough.round_int().to_dict())}
