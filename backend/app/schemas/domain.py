"""Domain objects produced when mapping AI output."""

from __future__ import annotations

from dataclasses import dataclass, field


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
    required_low: float = 0.0
    required_high: float = 0.0
    optional_low: float = 0.0
    optional_high: float = 0.0
    unknown_items: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    component_breakdown: list[dict[str, object]] = field(default_factory=list)
    pricing_debug_table: list[dict[str, object]] = field(default_factory=list)
    calculator_version: str = ""
