"""Cost estimation result schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["low", "medium", "high"]


class CostRangeOut(BaseModel):
    low: float
    high: float


class ProviderCostMatrixOut(BaseModel):
    aws: CostRangeOut = Field(default_factory=lambda: CostRangeOut(low=0, high=0))
    gcp: CostRangeOut = Field(default_factory=lambda: CostRangeOut(low=0, high=0))
    azure: CostRangeOut = Field(default_factory=lambda: CostRangeOut(low=0, high=0))


class CloudInfrastructureCostOut(BaseModel):
    categories: dict[str, ProviderCostMatrixOut] = Field(default_factory=dict)
    provider_totals: dict[str, CostRangeOut] = Field(default_factory=dict)


class CostBreakdownOut(BaseModel):
    cloud_infrastructure: CloudInfrastructureCostOut = Field(
        default_factory=CloudInfrastructureCostOut
    )
    cloud_cost: dict[str, CostRangeOut] = Field(default_factory=dict)
    ai_services_cost: dict[str, CostRangeOut] = Field(default_factory=dict)
    external_services_cost: dict[str, CostRangeOut] = Field(default_factory=dict)
    total_monthly_cost: CostRangeOut
    assumptions: list[str] = Field(default_factory=list)
    unknown_items: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "medium"
    disclaimer: str = ""
    currency: str = "USD"

    def model_post_init(self, __context: object) -> None:
        """Backfill cloud_infrastructure from legacy cloud_cost-only payloads."""
        if self.cloud_infrastructure.categories:
            if not self.cloud_infrastructure.provider_totals and self.cloud_cost:
                self.cloud_infrastructure.provider_totals = dict(self.cloud_cost)
            return

        if not self.cloud_cost:
            return

        has_nonzero = any(
            range_out.low > 0 or range_out.high > 0 for range_out in self.cloud_cost.values()
        )
        if not has_nonzero:
            return

        self.cloud_infrastructure.provider_totals = dict(self.cloud_cost)
        summary = ProviderCostMatrixOut()
        for provider, range_out in self.cloud_cost.items():
            if provider in {"aws", "gcp", "azure"}:
                setattr(summary, provider, range_out)
        self.cloud_infrastructure.categories = {"infrastructure_summary": summary}


@dataclass
class CostRange:
    low: float = 0.0
    high: float = 0.0

    def add(self, low: float, high: float) -> None:
        self.low += low
        self.high += high

    def scale(self, factor: float) -> CostRange:
        return CostRange(low=self.low * factor, high=self.high * factor)

    def round_int(self) -> CostRange:
        return CostRange(low=round(self.low), high=round(self.high))

    def to_dict(self) -> dict[str, float]:
        rounded = self.round_int()
        return {"low": float(rounded.low), "high": float(rounded.high)}


@dataclass
class UsageProfile:
    expected_users: str = "100"
    stage: str = "mvp"
    file_uploads: bool = False
    files_per_month: str = "under_1k"
    average_file_size: str = "small"
    process_after_upload: bool = False
    ai: bool = False
    ai_types: list[str] = field(default_factory=list)
    ai_requests_per_day: str = "under_100"
    notifications: bool = False
    payments: bool = False
    external_integrations: bool = False
    real_time: bool = False
    real_time_types: list[str] = field(default_factory=list)
    dashboards: bool = False
    authentication: bool = False
    has_intake_features: bool = False
    explicit_fields: frozenset[str] = field(default_factory=frozenset)
