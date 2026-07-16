"""Pydantic models for Step 4 (progressive cloud pricing)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PricingStatus = Literal["pending", "calculating", "completed", "failed"]
PricingLineItemStatus = Literal["priced", "skipped", "failed"]


class PricingFormulaLine(BaseModel):
    """One cost line from a pricing script formula breakdown."""

    model_config = ConfigDict(extra="forbid")

    label: str
    formula: str
    amount: float


class PricingCalculationDetails(BaseModel):
    """Transparent breakdown of how a line-item monthly price was calculated."""

    model_config = ConfigDict(extra="forbid")

    inputs: dict[str, Any] = Field(default_factory=dict)
    derived: dict[str, Any] = Field(default_factory=dict)
    free_tier: dict[str, Any] = Field(default_factory=dict)
    billable: dict[str, Any] = Field(default_factory=dict)
    formula_breakdown: list[PricingFormulaLine] = Field(default_factory=list)
    monthly_price: float = 0.0


class PricingLineItem(BaseModel):
    """A single component row for one cloud provider pricing result."""

    model_config = ConfigDict(extra="forbid")

    instance_id: str
    category_id: str
    component_name: str
    service_id: str | None = None
    service_name: str | None = None
    service_type: str | None = None
    monthly_price: float | None = None
    status: PricingLineItemStatus = "priced"
    skip_reason: str | None = None
    selection_reason: str | None = None
    calculation_summary: list[str] = Field(default_factory=list)
    details: PricingCalculationDetails | None = None


class ProviderPricingResult(BaseModel):
    """Pricing outcome for one cloud provider within a run."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    provider_label: str
    status: PricingStatus
    line_items: list[PricingLineItem] = Field(default_factory=list)
    monthly_total: float = 0.0
    error: str | None = None


class ProviderPricingResponse(BaseModel):
    """Response returned after generating pricing for a single provider."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    selection_id: str
    usage_model_id: str
    result: ProviderPricingResult


class PricingComparisonRow(BaseModel):
    """One row in the final provider comparison table."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    provider_label: str
    monthly_total: float | None = None
    status: PricingStatus


class PricingRunResponse(BaseModel):
    """Full pricing run state (all providers)."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    selection_id: str
    usage_model_id: str
    providers: list[ProviderPricingResult]
    comparison: list[PricingComparisonRow]

    @classmethod
    def from_stored_run(
        cls,
        run: dict[str, Any],
        provider_results: list[dict[str, Any]],
    ) -> PricingRunResponse:
        from app.config.params import CLOUD_PROVIDER_LABELS, PRICING_GENERATION_ORDER

        results_by_provider = {
            document.get("provider"): document for document in provider_results
        }

        providers: list[ProviderPricingResult] = []
        comparison: list[PricingComparisonRow] = []

        for provider in PRICING_GENERATION_ORDER:
            stored = results_by_provider.get(provider)
            if stored is None:
                result = ProviderPricingResult(
                    provider=provider,
                    provider_label=CLOUD_PROVIDER_LABELS.get(provider, provider),
                    status="pending",
                )
            else:
                line_items = []
                for item in stored.get("line_items", []):
                    parsed = PricingLineItem.model_validate(item)
                    if parsed.status == "priced" and parsed.monthly_price is None:
                        parsed = parsed.model_copy(
                            update={
                                "monthly_price": 0.0,
                                "status": "priced",
                            }
                        )
                    line_items.append(parsed)
                result = ProviderPricingResult(
                    provider=provider,
                    provider_label=CLOUD_PROVIDER_LABELS.get(provider, provider),
                    status=stored.get("status", "pending"),
                    line_items=line_items,
                    monthly_total=float(stored.get("monthly_total", 0) or 0),
                    error=stored.get("error"),
                )
            providers.append(result)
            comparison.append(
                PricingComparisonRow(
                    provider=provider,
                    provider_label=result.provider_label,
                    monthly_total=(
                        result.monthly_total
                        if result.status == "completed"
                        else None
                    ),
                    status=result.status,
                )
            )

        return cls(
            run_id=run["id"],
            selection_id=run.get("selection_id", ""),
            usage_model_id=run.get("usage_model_id", ""),
            providers=providers,
            comparison=comparison,
        )
