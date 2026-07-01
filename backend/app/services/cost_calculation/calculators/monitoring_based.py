"""Monitoring, metrics, and log ingestion pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_MONITORING
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class MonitoringBasedCalculator(BaseCostCalculator):
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        metric_samples = context.usage.get("metric_samples", 0.0)
        log_gb = context.usage.get("log_gb", 0.0)
        builder = AuditBuilder(record, context, PRICING_MODEL_MONITORING)

        builder.add_line("logs_ingested_gb", log_gb, quantity_note=f"log_gb({log_gb})")
        builder.add_line(
            "metrics",
            metric_samples / 1_000,
            quantity_note=f"metric_samples({metric_samples}) / 1_000",
        )

        return builder.build()
