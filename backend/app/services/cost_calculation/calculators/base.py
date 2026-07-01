"""Base calculator contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.cost_calculation.models import (
    CalculationContext,
    CostCalculationResult,
    PricingCatalogRecord,
)


class BaseCostCalculator(ABC):
    @abstractmethod
    def calculate(self, record: PricingCatalogRecord, context: CalculationContext) -> CostCalculationResult:
        raise NotImplementedError

    @staticmethod
    def sku_unit_price(record: PricingCatalogRecord, role: str) -> float | None:
        sku = record.skus.get(role)
        if not sku:
            return None
        price = sku.get("unit_price_usd")
        if price is None:
            return None
        return float(price)
