"""Domain objects produced when mapping AI output."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MappedComponent:
    key: str
    name: str
    component_type: str
    reason: str
    category: str
    optional: bool
    order: int
    cloud: dict[str, str | None]
    source: str = "ai_generated"


@dataclass
class ProviderCost:
    provider: str
    monthly_low: float
    monthly_high: float
    currency: str
    notes: str
