"""Helper for building auditable SKU line items during cost calculation."""

from __future__ import annotations

from typing import Any

from app.services.cost_calculation.models import (
    CalculationContext,
    CostCalculationResult,
    PricingCatalogRecord,
    SkuLineItem,
)
from app.services.cost_calculation.sku_roles import (
    ALLOWED_SKU_ROLES,
    ignored_catalog_roles,
    resolve_catalog_sku,
)


class AuditBuilder:
    def __init__(
        self,
        record: PricingCatalogRecord,
        context: CalculationContext,
        pricing_model: str,
    ) -> None:
        self._record = record
        self._context = context
        self._pricing_model = pricing_model
        self._lines: list[SkuLineItem] = []
        self._warnings: list[str] = []

    def warn_ignored_catalog_skus(self) -> None:
        for catalog_role in ignored_catalog_roles(self._pricing_model, self._record.skus):
            sku = self._record.skus[catalog_role]
            name = _sku_display_name(sku, catalog_role)
            self._warnings.append(
                f"Ignored unsupported SKU role '{catalog_role}' ({name}) "
                f"for pricing model '{self._pricing_model}'"
            )

    def add_line(
        self,
        role: str,
        quantity: float,
        *,
        quantity_note: str,
    ) -> float:
        resolved = resolve_catalog_sku(self._record.skus, role)
        if resolved is None:
            self._warnings.append(
                f"Required SKU role '{role}' not found in pricing record '{self._record.name}'"
            )
            self._lines.append(
                SkuLineItem(
                    sku_role=role,
                    sku_name=None,
                    sku_id=None,
                    usage_unit=None,
                    unit_price=None,
                    calculated_quantity=quantity,
                    quantity_note=quantity_note,
                    line_item_cost=0.0,
                )
            )
            return 0.0

        catalog_role, sku = resolved
        return self._add_sku_line(
            canonical_role=role,
            catalog_role=catalog_role,
            sku=sku,
            quantity=quantity,
            quantity_note=quantity_note,
        )

    def _add_sku_line(
        self,
        *,
        canonical_role: str,
        catalog_role: str,
        sku: dict[str, Any],
        quantity: float,
        quantity_note: str,
    ) -> float:
        unit_price = sku.get("unit_price_usd")
        sku_name = _sku_display_name(sku, catalog_role)
        if unit_price is None:
            self._warnings.append(
                f"SKU '{catalog_role}' ({sku_name}) has no unit_price_usd in '{self._record.name}'"
            )
            self._lines.append(
                SkuLineItem(
                    sku_role=canonical_role,
                    sku_name=sku_name,
                    sku_id=sku.get("sku_id"),
                    usage_unit=sku.get("usage_unit"),
                    unit_price=None,
                    calculated_quantity=quantity,
                    quantity_note=quantity_note,
                    line_item_cost=0.0,
                )
            )
            return 0.0

        price = float(unit_price)
        line_cost = quantity * price
        self._lines.append(
            SkuLineItem(
                sku_role=canonical_role,
                sku_name=sku_name,
                sku_id=sku.get("sku_id"),
                usage_unit=sku.get("usage_unit"),
                unit_price=price,
                calculated_quantity=quantity,
                quantity_note=quantity_note,
                line_item_cost=line_cost,
            )
        )
        return line_cost

    def warn(self, message: str) -> None:
        self._warnings.append(message)

    def build(self) -> CostCalculationResult:
        self.warn_ignored_catalog_skus()
        total = sum(line.line_item_cost for line in self._lines)
        return CostCalculationResult(
            monthly_cost=max(0.0, total),
            pricing_model=self._pricing_model,
            usage_assumptions=dict(self._context.usage),
            sku_lines=list(self._lines),
            warnings=list(self._warnings),
        )


def _sku_display_name(sku: dict[str, Any], fallback: str) -> str:
    for key in ("description", "name", "sku_name", "sku_id"):
        value = sku.get(key)
        if value:
            return str(value)
    return fallback
