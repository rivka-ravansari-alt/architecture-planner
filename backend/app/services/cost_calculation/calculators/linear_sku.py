"""Generic per-SKU linear pricing."""

from __future__ import annotations

from app.config.params import PRICING_MODEL_LINEAR_SKU
from app.services.cost_calculation.audit_builder import AuditBuilder
from app.services.cost_calculation.calculators.base import BaseCostCalculator
from app.services.cost_calculation.models import CalculationContext, CostCalculationResult, PricingCatalogRecord


class LinearSkuCalculator(BaseCostCalculator):
    _ROLE_USAGE_KEYS: dict[str, tuple[str, ...]] = {
        "storage": ("storage_gb", "database_storage_gb"),
        "egress": ("outbound_network_gb", "egress_gb"),
        "requests": ("monthly_requests",),
        "cpu": ("cpu_seconds", "instance_hours"),
        "memory": ("memory_gib_seconds",),
        "duration": ("memory_gib_seconds",),
        "reads": ("database_reads",),
        "writes": ("database_writes",),
        "input_tokens": ("input_tokens",),
        "output_tokens": ("output_tokens",),
        "usage": ("monthly_requests", "instances"),
    }

    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        builder = AuditBuilder(record, context, PRICING_MODEL_LINEAR_SKU)

        for role in record.skus:
            quantity, note = self._quantity_for_role(role, context.usage)
            if role == "cpu" and "cpu_seconds" in context.usage:
                quantity = context.usage["cpu_seconds"] / 3600.0
                note = f"cpu_seconds({context.usage['cpu_seconds']}) / 3600"
            builder.add_line(role, quantity, quantity_note=note)

        return builder.build()

    def _quantity_for_role(self, role: str, usage: dict[str, float]) -> tuple[float, str]:
        for key in self._ROLE_USAGE_KEYS.get(role, (role, f"{role}_gb", "quantity")):
            if key in usage and usage[key]:
                value = float(usage[key])
                return value, f"{key}({value})"
        return 0.0, "no matching usage (0)"
