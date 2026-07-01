"""Object / blob storage pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_STORAGE
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class StorageBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        storage_gb = context.usage.get("storage_gb", 0.0)
        builder = AuditBuilder(record, context, PRICING_MODEL_STORAGE)
        builder.add_line("storage", storage_gb, quantity_note=f"storage_gb({storage_gb})")
        return builder.build()
