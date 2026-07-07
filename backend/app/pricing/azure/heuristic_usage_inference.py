"""Heuristic usage assumption inference (compatibility shim)."""

from __future__ import annotations

from app.models import Project
from app.pricing.azure.usage_model_builder import AzureUsageModelBuilder
from app.pricing.schemas import ComponentPricingInput
from app.pricing.usage.context_builder import UsageContextBuilder
from app.pricing.usage.inference.fallback.heuristic_provider import (
    HEURISTIC_FALLBACK_REASONING,
    HeuristicFallbackProvider,
)
from app.pricing.usage.registry.azure import AzurePricingModelRegistry
from app.schemas.domain import MappedComponent

__all__ = ["HEURISTIC_FALLBACK_REASONING", "HeuristicUsageInference"]


class HeuristicUsageInference:
    """Backward-compatible wrapper around HeuristicFallbackProvider."""

    def __init__(self, *, usage_builder=None) -> None:
        builder = usage_builder or AzureUsageModelBuilder()
        self._usage_builder = builder
        self._provider = HeuristicFallbackProvider(
            usage_builders={"azure": builder},
            registries={"azure": AzurePricingModelRegistry()},
        )
        self._context_builder = UsageContextBuilder()

    def infer_components(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
        reasoning: str = HEURISTIC_FALLBACK_REASONING,
    ) -> list[ComponentPricingInput]:
        if reasoning != HEURISTIC_FALLBACK_REASONING:
            self._provider = HeuristicFallbackProvider(
                usage_builders={"azure": self._usage_builder},
                registries={"azure": AzurePricingModelRegistry()},
                reasoning=reasoning,
            )
        context = self._context_builder.build(
            project,
            components,
            feature_flags=feature_flags,
        )
        result = self._provider.infer(context)
        return list(result.components)

    def infer_component(
        self,
        project: Project,
        component: MappedComponent,
        *,
        profile=None,
        reasoning: str = HEURISTIC_FALLBACK_REASONING,
    ) -> ComponentPricingInput | None:
        results = self.infer_components(
            project,
            [component],
            reasoning=reasoning,
        )
        return results[0] if results else None
