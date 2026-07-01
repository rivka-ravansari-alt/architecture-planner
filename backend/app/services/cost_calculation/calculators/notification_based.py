"""Push / email notification pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_NOTIFICATION
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class NotificationBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        usage = context.usage
        emails = usage.get("emails_sent", 0.0)
        push = usage.get("push_notifications", 0.0)
        sms = usage.get("sms_messages", 0.0)
        builder = AuditBuilder(record, context, PRICING_MODEL_NOTIFICATION)

        builder.add_line("email", emails / 1_000, quantity_note=f"emails_sent({emails}) / 1_000")
        builder.add_line("sms", sms, quantity_note=f"sms_messages({sms})")
        builder.add_line("push", push / 1_000, quantity_note=f"push_notifications({push}) / 1_000")

        return builder.build()
