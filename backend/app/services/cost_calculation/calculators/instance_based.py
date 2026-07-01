"""Always-on instance / VM pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_INSTANCE
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class InstanceBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        instances = context.usage.get("instances", 0.0)
        instance_hours = context.usage.get("instance_hours", 0.0)
        builder = AuditBuilder(record, context, PRICING_MODEL_INSTANCE)

        builder.add_line("instance", instances, quantity_note=f"instances({instances})")
        builder.add_line("hour", instance_hours, quantity_note=f"instance_hours({instance_hours})")

        return builder.build()
