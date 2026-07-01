"""Convert normalized resource consumption into provider-specific monthly cost."""

from __future__ import annotations

from app.services.cost_calculation.factory import CostCalculatorFactory
from app.services.cost_calculation.models import (
    CalculationContext,
    CostCalculationResult,
    PricingCatalogRecord,
    PricingProfile,
)


class PricingEngine:
    """Applies pricing profiles and Firestore catalog SKU prices to usage metrics."""

    def __init__(self, *, calculator_factory: CostCalculatorFactory | None = None) -> None:
        self._factory = calculator_factory or CostCalculatorFactory()

    def calculate(
        self,
        record: PricingCatalogRecord,
        profile: PricingProfile,
        *,
        provider: str,
        expected_users: str,
        stage: str,
        usage_metrics: dict[str, float],
    ) -> CostCalculationResult:
        model = self._factory.resolve_model(profile)
        calculator = self._factory.for_profile(profile)
        context = CalculationContext(
            provider=provider,
            expected_users=expected_users,
            stage=stage,
            usage=usage_metrics,
        )

        if calculator is None:
            return CostCalculationResult(
                monthly_cost=0.0,
                pricing_model=model,
                usage_assumptions=dict(usage_metrics),
                warnings=[
                    f"Unsupported or disabled pricing model '{model}' "
                    f"for profile '{profile.service_name}' — no cost calculated"
                ],
                unsupported=True,
                pricing_profile_id=profile.id,
                pricing_profile_service=profile.service_name,
                billable_sku_roles=sorted(profile.billable_skus.keys()),
                ignored_sku_roles=list(profile.ignored_sku_roles),
            )

        return calculator.calculate(record, context)
