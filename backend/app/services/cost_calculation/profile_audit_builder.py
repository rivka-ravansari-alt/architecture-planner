"""Build auditable SKU line items from pricing profiles and catalog SKUs."""

from __future__ import annotations

from typing import Any

from app.services.cost_calculation.models import (
    CalculationContext,
    CostCalculationResult,
    PricingCatalogRecord,
    PricingProfile,
    SkuLineItem,
)
from app.services.cost_calculation.sku_roles import resolve_catalog_sku
from app.services.cost_calculation.unit_conversions import (
    UnsupportedConversionError,
    apply_conversion,
)


class ProfileAuditBuilder:
    def __init__(
        self,
        record: PricingCatalogRecord,
        profile: PricingProfile,
        context: CalculationContext,
    ) -> None:
        self._record = record
        self._profile = profile
        self._context = context
        self._lines: list[SkuLineItem] = []
        self._warnings: list[str] = []
        self._missing_catalog_skus = False

    def calculate(self) -> CostCalculationResult:
        ignored_catalog = set(role.casefold() for role in self._profile.ignored_sku_roles)
        billable_roles = set(self._profile.billable_skus.keys())

        for catalog_role in self._record.skus:
            if catalog_role.casefold() in ignored_catalog:
                continue
            if catalog_role not in billable_roles:
                sku = self._record.skus[catalog_role]
                name = _sku_display_name(sku, catalog_role)
                self._warnings.append(
                    f"Ignored catalog SKU role '{catalog_role}' ({name}) "
                    f"not listed in pricing profile billable_skus"
                )

        for role, config in self._profile.billable_skus.items():
            if role.casefold() in ignored_catalog:
                continue

            raw_value = self._context.usage.get(config.usage_metric, 0.0)
            try:
                quantity, conversion_note = apply_conversion(raw_value, config.conversion)
            except UnsupportedConversionError as exc:
                self._warnings.append(
                    f"Billable SKU role '{role}': {exc}"
                )
                self._missing_catalog_skus = True
                continue

            quantity_note = f"{config.usage_metric}({raw_value}) -> {conversion_note}"
            self._add_billable_line(
                role=role,
                quantity=quantity,
                quantity_note=quantity_note,
                usage_metric=config.usage_metric,
                conversion=config.conversion,
            )

        total = sum(line.line_item_cost for line in self._lines)
        return CostCalculationResult(
            monthly_cost=max(0.0, total),
            pricing_model=self._profile.pricing_model,
            usage_assumptions=dict(self._context.usage),
            sku_lines=list(self._lines),
            warnings=list(self._warnings),
            missing_catalog_skus=self._missing_catalog_skus,
            pricing_profile_id=self._profile.id,
            pricing_profile_service=self._profile.service_name,
            billable_sku_roles=sorted(self._profile.billable_skus.keys()),
            ignored_sku_roles=list(self._profile.ignored_sku_roles),
        )

    def _add_billable_line(
        self,
        *,
        role: str,
        quantity: float,
        quantity_note: str,
        usage_metric: str,
        conversion: str,
    ) -> float:
        resolved = resolve_catalog_sku(self._record.skus, role)
        if resolved is None:
            self._missing_catalog_skus = True
            self._warnings.append(
                f"Required billable SKU role '{role}' not found in catalog '{self._record.name}'"
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
                    usage_metric=usage_metric,
                    conversion=conversion,
                )
            )
            return 0.0

        catalog_role, sku = resolved
        return self._add_sku_line(
            role=role,
            catalog_role=catalog_role,
            sku=sku,
            quantity=quantity,
            quantity_note=quantity_note,
            usage_metric=usage_metric,
            conversion=conversion,
        )

    def _add_sku_line(
        self,
        *,
        role: str,
        catalog_role: str,
        sku: dict[str, Any],
        quantity: float,
        quantity_note: str,
        usage_metric: str,
        conversion: str,
    ) -> float:
        unit_price = sku.get("unit_price_usd")
        sku_name = _sku_display_name(sku, catalog_role)
        if unit_price is None:
            self._missing_catalog_skus = True
            self._warnings.append(
                f"SKU '{catalog_role}' ({sku_name}) has no unit_price_usd in '{self._record.name}'"
            )
            self._lines.append(
                SkuLineItem(
                    sku_role=role,
                    sku_name=sku_name,
                    sku_id=sku.get("sku_id"),
                    usage_unit=sku.get("usage_unit"),
                    unit_price=None,
                    calculated_quantity=quantity,
                    quantity_note=quantity_note,
                    line_item_cost=0.0,
                    usage_metric=usage_metric,
                    conversion=conversion,
                )
            )
            return 0.0

        price = float(unit_price)
        line_cost = quantity * price
        self._lines.append(
            SkuLineItem(
                sku_role=role,
                sku_name=sku_name,
                sku_id=sku.get("sku_id"),
                usage_unit=sku.get("usage_unit"),
                unit_price=price,
                calculated_quantity=quantity,
                quantity_note=quantity_note,
                line_item_cost=line_cost,
                usage_metric=usage_metric,
                conversion=conversion,
            )
        )
        return line_cost


def _sku_display_name(sku: dict[str, Any], fallback: str) -> str:
    for key in ("description", "name", "sku_name", "sku_id"):
        value = sku.get(key)
        if value:
            return str(value)
    return fallback
