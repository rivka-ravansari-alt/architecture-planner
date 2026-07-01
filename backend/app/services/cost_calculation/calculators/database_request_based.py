"""Database request / throughput pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_DATABASE_REQUEST
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class DatabaseRequestBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        usage = context.usage
        database_reads = usage.get("database_reads", 0.0)
        database_writes = usage.get("database_writes", 0.0)
        storage_gb = usage.get("database_storage_gb", usage.get("storage_gb", 0.0))
        reads = database_reads / 1_000_000
        writes = database_writes / 1_000_000

        builder = AuditBuilder(record, context, PRICING_MODEL_DATABASE_REQUEST)

        builder.add_line(
            "reads",
            reads,
            quantity_note=f"database_reads({database_reads}) / 1_000_000",
        )
        builder.add_line(
            "writes",
            writes,
            quantity_note=f"database_writes({database_writes}) / 1_000_000",
        )
        builder.add_line(
            "storage",
            storage_gb,
            quantity_note=f"database_storage_gb({storage_gb})",
        )

        return builder.build()
