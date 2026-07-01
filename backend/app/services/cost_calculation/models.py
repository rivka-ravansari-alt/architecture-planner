"""Domain models for cost calculation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PricingCatalogRecord:
    id: str
    name: str
    provider: str
    skus: dict[str, dict[str, Any]]
    formula: dict[str, str] | str


@dataclass(frozen=True)
class BillableSkuConfig:
    usage_metric: str
    conversion: str = "none"


@dataclass(frozen=True)
class PricingProfile:
    id: str
    provider: str
    service_name: str
    pricing_model: str
    billable_skus: dict[str, BillableSkuConfig]
    ignored_sku_roles: tuple[str, ...] = ()
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "service_name": self.service_name,
            "pricing_model": self.pricing_model,
            "billable_skus": {
                role: {
                    "usage_metric": config.usage_metric,
                    "conversion": config.conversion,
                }
                for role, config in self.billable_skus.items()
            },
            "ignored_sku_roles": list(self.ignored_sku_roles),
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class CalculationContext:
    provider: str
    expected_users: str
    stage: str
    usage: dict[str, float]


@dataclass(frozen=True)
class SkuLineItem:
    sku_role: str
    sku_id: str | None
    usage_unit: str | None
    unit_price: float | None
    calculated_quantity: float
    quantity_note: str
    line_item_cost: float
    sku_name: str | None = None
    usage_metric: str | None = None
    conversion: str | None = None


@dataclass
class CostCalculationResult:
    monthly_cost: float
    pricing_model: str
    usage_assumptions: dict[str, float]
    sku_lines: list[SkuLineItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported: bool = False
    missing_catalog_skus: bool = False
    pricing_profile_id: str | None = None
    pricing_profile_service: str | None = None
    billable_sku_roles: list[str] = field(default_factory=list)
    ignored_sku_roles: list[str] = field(default_factory=list)


@dataclass
class ComponentCostAudit:
    component_key: str
    component_name: str
    component_type: str
    service_name: str
    pricing_record_id: str
    pricing_record_name: str
    pricing_model: str
    formula: dict[str, str] | str
    expected_users: str
    usage_assumptions: dict[str, float]
    sku_lines: list[SkuLineItem]
    final_component_cost: float
    optional: bool
    pricing_profile_id: str
    pricing_profile_service: str
    billable_sku_roles: list[str] = field(default_factory=list)
    ignored_sku_roles: list[str] = field(default_factory=list)
    calculation_warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComponentCostLine:
    component_key: str
    component_name: str
    component_type: str
    service_name: str
    monthly_cost: float
    optional: bool
    audit: ComponentCostAudit | None = None


@dataclass
class ProviderCostResult:
    provider: str
    required_total: float
    optional_total: float
    currency: str
    unknown_items: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    component_lines: list[ComponentCostLine] = field(default_factory=list)
    pricing_debug_table: list[dict[str, object]] = field(default_factory=list)
    calculator_version: str = ""

    @property
    def total(self) -> float:
        return self.required_total + self.optional_total
