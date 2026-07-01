"""LLM / token-based pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_TOKEN
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class TokenBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        usage = context.usage
        input_tokens = usage.get("input_tokens", 0.0)
        output_tokens = usage.get("output_tokens", 0.0)
        input_qty = input_tokens / 1_000
        output_qty = output_tokens / 1_000

        builder = AuditBuilder(record, context, PRICING_MODEL_TOKEN)

        builder.add_line(
            "input_tokens",
            input_qty,
            quantity_note=f"input_tokens({input_tokens}) / 1_000",
        )
        builder.add_line(
            "output_tokens",
            output_qty,
            quantity_note=f"output_tokens({output_tokens}) / 1_000",
        )

        return builder.build()
