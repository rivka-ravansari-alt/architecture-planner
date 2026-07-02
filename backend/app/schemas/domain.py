"""Domain objects produced when mapping AI output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class RequirementContext:
    """User requirements that drive usage volume assumptions."""

    auth: bool = False
    file_upload: bool = False
    background_processing: bool = False
    ai: bool = False
    dashboards: bool = False
    payments: bool = False


@dataclass
class MatchedSku:
    role: str
    sku_id: str
    description: str
    usage_unit: str
    unit_price_usd: float
    quantity: float
    free_tier_applied: float
    cost_usd: float


@dataclass
class ComponentCostEstimate:
    component_name: str
    component_type: str
    component_key: str
    cloud_provider: str
    cloud_service: str
    optional: bool
    matched_skus: list[MatchedSku]
    usage_assumptions: dict[str, Any]
    monthly_cost_min: float
    monthly_cost_max: float
    calculation_explanation: str
    confidence: Literal["high", "medium", "low"]
    missing_data: list[str] = field(default_factory=list)
    pricing_audit: dict[str, Any] = field(default_factory=dict)


@dataclass
class MappedComponent:
    key: str
    name: str
    component_type: str
    reason: str
    category: str
    optional: bool
    order: int
    cloud: dict[str, list[str]]
    implementation_options: dict[str, object]
    source: str = "ai_generated"


@dataclass
class ProviderCost:
    provider: str
    monthly_low: float
    monthly_high: float
    currency: str
    notes: str
    component_costs: list[ComponentCostEstimate] = field(default_factory=list)
