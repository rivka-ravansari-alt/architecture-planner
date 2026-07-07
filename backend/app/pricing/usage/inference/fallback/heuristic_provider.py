"""Heuristic usage assumption inference (fallback when LLM is unavailable)."""

from __future__ import annotations

from typing import Protocol

from app.models import Project
from app.pricing.assumptions import coerce_value, resolve_usage_assumptions
from app.pricing.aws.usage_model_builder import AwsUsageModelBuilder
from app.pricing.azure.usage_model_builder import AzureUsageModelBuilder
from app.pricing.gcp.usage_model_builder import GcpUsageModelBuilder
from app.pricing.schemas import (
    AssumptionConfidence,
    AssumptionSource,
    ComponentPricingInput,
    UsageAssumption,
)
from app.pricing.usage.inference.fallback._helpers import (
    components_from_context,
    project_from_context,
)
from app.pricing.usage.protocols import PricingModelRegistry, UsageInferenceProvider
from app.pricing.usage.registry.aws import AwsPricingModelRegistry
from app.pricing.usage.registry.azure import AzurePricingModelRegistry
from app.pricing.usage.registry.gcp import GcpPricingModelRegistry
from app.pricing.usage.schemas import CloudProvider, UsageContext, UsageInferenceAudit, UsageInferenceResult

HEURISTIC_FALLBACK_REASONING = (
    "Heuristic fallback: estimated from user scale bands and architecture topology "
    "because LLM inference was unavailable."
)


class _UsageModelBuilder(Protocol):
    def build_profile(
        self,
        project: Project,
        components: list,
        *,
        feature_flags: dict[str, bool] | None = None,
    ): ...

    def build_for_component(self, profile, component, service_name: str) -> dict: ...


_BUILDERS: dict[CloudProvider, _UsageModelBuilder] = {
    "azure": AzureUsageModelBuilder(),
    "aws": AwsUsageModelBuilder(),
    "gcp": GcpUsageModelBuilder(),
}

_REGISTRIES: dict[CloudProvider, PricingModelRegistry] = {
    "azure": AzurePricingModelRegistry(),
    "aws": AwsPricingModelRegistry(),
    "gcp": GcpPricingModelRegistry(),
}


class HeuristicFallbackProvider(UsageInferenceProvider):
    """Derive usage assumptions from scale bands and architecture topology."""

    def __init__(
        self,
        *,
        usage_builders: dict[CloudProvider, _UsageModelBuilder] | None = None,
        registries: dict[CloudProvider, PricingModelRegistry] | None = None,
        reasoning: str = HEURISTIC_FALLBACK_REASONING,
    ) -> None:
        self._usage_builders = usage_builders or dict(_BUILDERS)
        self._registries = registries or dict(_REGISTRIES)
        self._reasoning = reasoning

    def infer(self, context: UsageContext) -> UsageInferenceResult:
        provider = context.provider
        usage_builder = self._usage_builders.get(provider)
        registry = self._registries.get(provider)
        if usage_builder is None or registry is None:
            return UsageInferenceResult(
                components=(),
                inference_source="heuristic_fallback",
                audit=UsageInferenceAudit(),
            )

        project = project_from_context(context)
        components = components_from_context(context)
        profile = usage_builder.build_profile(
            project,
            components,
            feature_flags=context.feature_flags,
        )

        results: list[ComponentPricingInput] = []
        for component_ctx in context.components:
            mapped = next(
                (item for item in components if item.key == component_ctx.component_id),
                None,
            )
            if mapped is None:
                continue

            model = registry.resolve_model(component_ctx.cloud.mapped_service_name)
            if model is None:
                continue

            derived = usage_builder.build_for_component(
                profile,
                mapped,
                model.service,
            )
            if not derived:
                continue

            inferred = self._assumptions_from_derived(derived, component_ctx, model.service)
            resolution = resolve_usage_assumptions(model, inferred=inferred)
            if not resolution.ready_for_calculation:
                gap_fill = self._fill_missing_with_defaults(
                    model,
                    component_ctx,
                    resolution.resolved,
                    resolution.missing,
                )
                merged = {item.key: item for item in resolution.resolved}
                merged.update(gap_fill)
                resolution = resolve_usage_assumptions(model, inferred=merged)

            results.append(
                ComponentPricingInput(
                    component_id=component_ctx.component_id,
                    order=component_ctx.order,
                    provider=provider,
                    cloud_service=model.service,
                    resolved=resolution.resolved,
                )
            )

        return UsageInferenceResult(
            components=tuple(sorted(results, key=lambda item: item.order)),
            inference_source="heuristic_fallback",
            audit=UsageInferenceAudit(),
        )

    def _assumptions_from_derived(
        self,
        derived: dict,
        component_ctx,
        model_service: str,
    ) -> dict[str, UsageAssumption]:
        input_defs = {item.key: item for item in component_ctx.required_inputs}
        inferred: dict[str, UsageAssumption] = {}
        for key, raw_value in derived.items():
            input_def = input_defs.get(key)
            if input_def is None:
                continue
            inferred[key] = UsageAssumption(
                key=key,
                value=coerce_value(raw_value, input_def),
                unit=input_def.unit,
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.low,
                reasoning=self._reasoning,
            )
        return inferred

    def _fill_missing_with_defaults(self, model, component_ctx, resolved, missing):
        resolved_keys = {item.key for item in resolved}
        input_defs = {item.key: item for item in component_ctx.required_inputs}
        inferred: dict[str, UsageAssumption] = {}
        for item in missing:
            if item.key in resolved_keys:
                continue
            default = model.pricing_model.default_values.get(item.key)
            input_def = input_defs.get(item.key)
            if default is None and input_def is not None:
                default = input_def.default_value
            if default is None or input_def is None:
                continue
            inferred[item.key] = UsageAssumption(
                key=item.key,
                value=coerce_value(default, input_def),
                unit=item.unit,
                source=AssumptionSource.inferred,
                confidence=AssumptionConfidence.low,
                reasoning=f"{self._reasoning} Default applied for {item.key}.",
            )
        return inferred
