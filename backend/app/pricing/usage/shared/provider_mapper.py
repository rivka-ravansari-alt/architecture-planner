"""Map shared LLM usage assumptions to provider-specific pricing inputs."""

from __future__ import annotations

import logging

from app.models import Project
from app.pricing.assumptions import resolve_usage_assumptions
from app.pricing.schemas import ComponentPricingInput, UsageAssumption
from app.pricing.usage.context_builder import UsageContextBuilder
from app.pricing.usage.inference.fallback.heuristic_provider import HeuristicFallbackProvider
from app.pricing.usage.scaling import scale_behavioral_assumptions
from app.pricing.usage.schemas import CloudProvider
from app.pricing.usage.shared.schemas import (
    ProviderUsageInferenceResult,
    SharedComponentInference,
    SharedUsageInferenceResult,
)
from app.pricing.usage.registry.aws import AwsPricingModelRegistry
from app.pricing.usage.registry.azure import AzurePricingModelRegistry
from app.pricing.usage.registry.gcp import GcpPricingModelRegistry
from app.schemas.domain import MappedComponent

logger = logging.getLogger(__name__)

_REGistries = {
    "azure": AzurePricingModelRegistry(),
    "aws": AwsPricingModelRegistry(),
    "gcp": GcpPricingModelRegistry(),
}


class SharedUsageProviderMapper:
    """Project shared LLM assumptions onto Azure, AWS, and GCP pricing models."""

    def __init__(
        self,
        *,
        fallback: HeuristicFallbackProvider | None = None,
        context_builder: UsageContextBuilder | None = None,
    ) -> None:
        self._fallback = fallback or HeuristicFallbackProvider()
        self._context_builder = context_builder or UsageContextBuilder()

    def map_all_providers(
        self,
        shared: SharedUsageInferenceResult,
        *,
        project: Project,
        components: list[MappedComponent],
        feature_flags: dict[str, bool] | None = None,
    ) -> dict[CloudProvider, ProviderUsageInferenceResult]:
        return {
            provider: self.map_provider(
                shared,
                provider=provider,
                project=project,
                components=components,
                feature_flags=feature_flags,
            )
            for provider in ("azure", "aws", "gcp")
        }

    def map_provider(
        self,
        shared: SharedUsageInferenceResult,
        *,
        provider: CloudProvider,
        project: Project,
        components: list[MappedComponent],
        feature_flags: dict[str, bool] | None = None,
    ) -> ProviderUsageInferenceResult:
        shared_by_id = {item.component_id: item for item in shared.components}
        mapped_by_id = {item.key: item for item in components}
        registry = _REGistries.get(provider)
        if registry is None:
            return self._heuristic_provider_fallback(
                provider,
                project,
                components,
                feature_flags,
                reason=f"No registry for provider {provider!r}.",
            )

        results: list[ComponentPricingInput] = []
        warnings: list[str] = []

        for shared_component in shared.components:
            mapped = mapped_by_id.get(shared_component.component_id)
            if mapped is None:
                continue
            mapped_service = mapped.cloud.get(provider)
            if not mapped_service:
                continue
            model = registry.resolve_model(str(mapped_service))
            if model is None:
                warnings.append(
                    f"Component {shared_component.component_id}: unsupported {provider} "
                    f"service {mapped_service!r}; skipped."
                )
                continue
            try:
                pricing_input = self._map_component(
                    shared_component,
                    provider=provider,
                    cloud_service=model.service,
                    expected_users=_expected_users(project),
                )
            except ValueError as exc:
                warnings.append(
                    f"Component {shared_component.component_id}: {exc}; "
                    f"falling back to heuristic for this provider."
                )
                return self._heuristic_provider_fallback(
                    provider,
                    project,
                    components,
                    feature_flags,
                    reason=str(exc),
                    partial_warnings=tuple(warnings),
                )
            results.append(pricing_input)

        if not results:
            return self._heuristic_provider_fallback(
                provider,
                project,
                components,
                feature_flags,
                reason=f"No {provider} components could be mapped from shared LLM assumptions.",
                partial_warnings=tuple(warnings),
            )

        missing_ids = {
            item.key
            for item in components
            if item.cloud.get(provider) and item.key not in {r.component_id for r in results}
        }
        if missing_ids:
            warnings.append(
                f"Shared LLM assumptions missing for {provider} components: "
                + ", ".join(sorted(missing_ids))
            )
            return self._heuristic_provider_fallback(
                provider,
                project,
                components,
                feature_flags,
                reason="Incomplete shared LLM coverage for mapped components.",
                partial_warnings=tuple(warnings),
            )

        return ProviderUsageInferenceResult(
            components=tuple(sorted(results, key=lambda item: item.order)),
            inference_source=shared.inference_source,
            warnings=tuple(warnings),
        )

    def _map_component(
        self,
        shared_component: SharedComponentInference,
        *,
        provider: CloudProvider,
        cloud_service: str,
        expected_users: int,
    ) -> ComponentPricingInput:
        behavioral = dict(shared_component.behavioral)
        config = dict(shared_component.config)
        for item in shared_component.storage_breakdown:
            if item.key in config:
                config[item.key] = item
            else:
                behavioral[item.key] = item

        try:
            scaled = scale_behavioral_assumptions(
                cloud_service,
                behavioral=behavioral,
                config=config,
                expected_users=expected_users,
            )
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        registry = _REGistries[provider]
        model = registry.resolve_model(cloud_service)
        if model is None:
            raise ValueError(f"Unknown pricing model for {cloud_service!r}")

        resolution = resolve_usage_assumptions(model, inferred=scaled)
        if not resolution.ready_for_calculation:
            missing_keys = ", ".join(item.key for item in resolution.missing)
            raise ValueError(f"missing required assumptions: {missing_keys}")

        behavioral_list = list(behavioral.values()) + list(config.values())
        return ComponentPricingInput(
            component_id=shared_component.component_id,
            order=shared_component.order,
            provider=provider,
            cloud_service=cloud_service,
            resolved=resolution.resolved,
            behavioral_assumptions=sorted(behavioral_list, key=lambda item: item.key),
        )

    def _heuristic_provider_fallback(
        self,
        provider: CloudProvider,
        project: Project,
        components: list[MappedComponent],
        feature_flags: dict[str, bool] | None,
        *,
        reason: str,
        partial_warnings: tuple[str, ...] = (),
    ) -> ProviderUsageInferenceResult:
        logger.warning(
            "Shared LLM assumptions unavailable for %s; using heuristic fallback: %s",
            provider,
            reason,
        )
        context = self._context_builder.build(
            project,
            components,
            provider=provider,
            feature_flags=feature_flags,
        )
        fallback_result = self._fallback.infer(context)
        warnings = (*partial_warnings, f"Heuristic fallback for {provider}: {reason}")
        return ProviderUsageInferenceResult(
            components=fallback_result.components,
            inference_source="heuristic_fallback",
            warnings=warnings,
        )


def _expected_users(project: Project) -> int:
    return {
        "100": 100,
        "1000": 1_000,
        "10000": 10_000,
        "100000+": 100_000,
    }.get(project.expected_users or "100", 100)
