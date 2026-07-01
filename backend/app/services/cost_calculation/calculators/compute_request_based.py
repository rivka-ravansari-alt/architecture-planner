"""Serverless / request-driven compute pricing (Cloud Run, Lambda, etc.)."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_COMPUTE_REQUEST
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord

_SECONDS_PER_HOUR = 3600.0


class ComputeRequestBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        usage = context.usage
        monthly_requests = usage.get("monthly_requests", 0.0)
        cpu_seconds = usage.get("cpu_seconds", 0.0)
        memory_gib_seconds = usage.get("memory_gib_seconds", 0.0)
        cpu_vcpu_hours = cpu_seconds / _SECONDS_PER_HOUR
        memory_gib_hours = memory_gib_seconds / _SECONDS_PER_HOUR

        builder = AuditBuilder(record, context, PRICING_MODEL_COMPUTE_REQUEST)

        builder.add_line(
            "cpu",
            cpu_vcpu_hours,
            quantity_note=f"cpu_seconds({cpu_seconds}) / 3600 -> vcpu-hours",
        )
        builder.add_line(
            "memory",
            memory_gib_hours,
            quantity_note=f"memory_gib_seconds({memory_gib_seconds}) / 3600 -> gib-hours",
        )
        builder.add_line(
            "requests",
            monthly_requests / 1_000_000,
            quantity_note=f"monthly_requests({monthly_requests}) / 1_000_000",
        )

        return builder.build()
