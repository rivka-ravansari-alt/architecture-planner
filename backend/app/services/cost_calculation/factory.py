"""Select calculator implementation from pricing profile."""

from __future__ import annotations

from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.calculators.profile_driven import ProfileDrivenCalculator
from app.services.cost_calculation.models import PricingCatalogRecord, PricingProfile
from app.services.cost_calculation.sku_roles import SUPPORTED_PRICING_MODELS


class CostCalculatorFactory:
    def for_profile(self, profile: PricingProfile) -> BaseCostCalculator | None:
        if not profile.enabled:
            return None
        if profile.pricing_model not in SUPPORTED_PRICING_MODELS:
            return None
        return ProfileDrivenCalculator(profile)

    def resolve_model(self, profile: PricingProfile) -> str:
        return profile.pricing_model

    def for_record(self, record: PricingCatalogRecord) -> BaseCostCalculator | None:
        raise NotImplementedError(
            "Cost calculation requires a pricing profile; catalog formula is no longer used"
        )
