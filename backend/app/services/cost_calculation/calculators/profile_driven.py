"""Calculate monthly cost from a pricing profile and catalog SKU prices."""

from __future__ import annotations

import logging

from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import (
    CalculationContext,
    CostCalculationResult,
    PricingCatalogRecord,
    PricingProfile,
)
from app.services.cost_calculation.profile_audit_builder import ProfileAuditBuilder

logger = logging.getLogger(__name__)


class ProfileDrivenCalculator(BaseCostCalculator):
    def __init__(self, profile: PricingProfile) -> None:
        self._profile = profile

    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        logger.info(
            "PROFILE_DRIVEN_COST_CALCULATOR_USED provider=%s service=%s profile_id=%s model=%s",
            context.provider,
            self._profile.service_name,
            self._profile.id,
            self._profile.pricing_model,
        )
        return ProfileAuditBuilder(record, self._profile, context).calculate()
