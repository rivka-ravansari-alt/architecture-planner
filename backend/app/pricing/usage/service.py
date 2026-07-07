"""Facade for the cloud-agnostic usage assumptions layer."""

from __future__ import annotations

from typing import Literal

from app.clients.ai_client import BaseAIClient
from app.models import Project
from app.pricing.schemas import ComponentPricingInput
from app.pricing.usage.context_builder import UsageContextBuilder
from app.pricing.usage.inference.fallback.heuristic_provider import HeuristicFallbackProvider
from app.pricing.usage.inference.llm.provider import LLMUsageInferenceProvider
from app.pricing.usage.shared.context_builder import SharedUsageContextBuilder
from app.pricing.usage.shared.provider_mapper import SharedUsageProviderMapper
from app.pricing.usage.shared.prompt_builder import SharedUsageAssumptionsPromptBuilder
from app.pricing.usage.shared.response_validator import SharedUsageAssumptionsResponseValidator
from app.pricing.usage.protocols import UsageInferenceProvider
from app.pricing.usage.schemas import CloudProvider, UsageInferenceResult
from app.pricing.usage.shared.schemas import ProviderUsageInferenceResult, SharedUsageInferenceResult
from app.schemas.domain import MappedComponent

InferenceMode = Literal["llm", "heuristic"]


class UsageAssumptionsService:
    """Single entry point for usage assumption inference."""

    def __init__(
        self,
        *,
        context_builder: UsageContextBuilder | None = None,
        primary_provider: UsageInferenceProvider | None = None,
        fallback_provider: UsageInferenceProvider | None = None,
        ai_client: BaseAIClient | None = None,
        inference_mode: InferenceMode = "llm",
    ) -> None:
        self._context_builder = context_builder or UsageContextBuilder()
        self._shared_context_builder = SharedUsageContextBuilder()
        self._shared_prompt_builder = SharedUsageAssumptionsPromptBuilder()
        self._shared_validator = SharedUsageAssumptionsResponseValidator()
        self._fallback = fallback_provider or HeuristicFallbackProvider()
        self._shared_mapper = SharedUsageProviderMapper(fallback=self._fallback)
        self._inference_mode = inference_mode

        if primary_provider is not None:
            self._primary = primary_provider
        elif ai_client is not None:
            self._primary = LLMUsageInferenceProvider(ai_client=ai_client)
        else:
            self._primary = None

    @property
    def fallback(self) -> HeuristicFallbackProvider:
        if isinstance(self._fallback, HeuristicFallbackProvider):
            return self._fallback
        return HeuristicFallbackProvider()

    def infer(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        provider: CloudProvider = "azure",
        feature_flags: dict[str, bool] | None = None,
        inference_mode: InferenceMode | None = None,
    ) -> UsageInferenceResult:
        mode = inference_mode or self._inference_mode

        try:
            context = self._context_builder.build(
                project,
                components,
                provider=provider,
                feature_flags=feature_flags,
            )
        except ValueError:
            return UsageInferenceResult(
                components=(),
                inference_source="heuristic_only",
                audit=self._empty_audit(),
            )

        if mode == "heuristic" or self._primary is None:
            result = self._fallback.infer(context)
            return UsageInferenceResult(
                components=result.components,
                inference_source="heuristic_only",
                audit=result.audit,
            )

        if isinstance(self._primary, LLMUsageInferenceProvider):
            return self._primary.infer_with_fallback_on_error(context, self._fallback)

        return self._primary.infer(context)

    def build_prompt(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        provider: CloudProvider = "azure",
        feature_flags: dict[str, bool] | None = None,
    ) -> str:
        context = self._context_builder.build(
            project,
            components,
            provider=provider,
            feature_flags=feature_flags,
        )
        if not isinstance(self._primary, LLMUsageInferenceProvider):
            raise ValueError("LLM provider is not configured.")
        return self._primary.build_prompt(context)

    def parse_response(
        self,
        raw: str,
        project: Project,
        components: list[MappedComponent],
        *,
        provider: CloudProvider = "azure",
        feature_flags: dict[str, bool] | None = None,
    ) -> UsageInferenceResult:
        context = self._context_builder.build(
            project,
            components,
            provider=provider,
            feature_flags=feature_flags,
        )
        if not isinstance(self._primary, LLMUsageInferenceProvider):
            raise ValueError("LLM provider is not configured.")
        return self._primary.parse_response(raw, context)

    def infer_components(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        provider: CloudProvider = "azure",
        feature_flags: dict[str, bool] | None = None,
        inference_mode: InferenceMode | None = None,
    ) -> list[ComponentPricingInput]:
        """Backward-compatible helper returning only pricing inputs."""
        result = self.infer(
            project,
            components,
            provider=provider,
            feature_flags=feature_flags,
            inference_mode=inference_mode,
        )
        return list(result.components)

    def build_shared_prompt(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
    ) -> str:
        context = self._shared_context_builder.build(
            project,
            components,
            feature_flags=feature_flags,
        )
        return self._shared_prompt_builder.build(context)

    def parse_shared_response(
        self,
        raw: str,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
    ) -> SharedUsageInferenceResult:
        context = self._shared_context_builder.build(
            project,
            components,
            feature_flags=feature_flags,
        )
        return self._shared_validator.validate(raw, context)

    def map_shared_to_providers(
        self,
        shared: SharedUsageInferenceResult,
        *,
        project: Project,
        components: list[MappedComponent],
        feature_flags: dict[str, bool] | None = None,
    ) -> dict[CloudProvider, ProviderUsageInferenceResult]:
        return self._shared_mapper.map_all_providers(
            shared,
            project=project,
            components=components,
            feature_flags=feature_flags,
        )

    def infer_all_providers_heuristic(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
        inference_source: Literal["heuristic_fallback", "heuristic_only"] = "heuristic_fallback",
    ) -> dict[CloudProvider, ProviderUsageInferenceResult]:
        results: dict[CloudProvider, ProviderUsageInferenceResult] = {}
        for provider in ("azure", "aws", "gcp"):
            try:
                context = self._context_builder.build(
                    project,
                    components,
                    provider=provider,
                    feature_flags=feature_flags,
                )
            except ValueError:
                results[provider] = ProviderUsageInferenceResult(
                    components=(),
                    inference_source=inference_source,
                    warnings=(f"No {provider} components available for heuristic fallback.",),
                )
                continue
            fallback_result = self._fallback.infer(context)
            results[provider] = ProviderUsageInferenceResult(
                components=fallback_result.components,
                inference_source=inference_source,
                warnings=(f"All providers using {inference_source}.",),
            )
        return results

    @staticmethod
    def _empty_audit():
        from app.pricing.usage.schemas import UsageInferenceAudit

        return UsageInferenceAudit()
