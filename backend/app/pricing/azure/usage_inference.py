"""Infer Azure usage assumptions from project fields and component mappings."""

from __future__ import annotations

from app.clients.ai_client import BaseAIClient
from app.models import Project
from app.pricing.schemas import ComponentPricingInput
from app.pricing.usage.service import InferenceMode, UsageAssumptionsService
from app.schemas.domain import MappedComponent

__all__ = ["AzureUsageInferenceEngine", "InferenceMode"]


class AzureUsageInferenceEngine:
    """Facade delegating to UsageAssumptionsService."""

    def __init__(
        self,
        *,
        ai_client: BaseAIClient | None = None,
        usage_assumptions_service: UsageAssumptionsService | None = None,
        inference_mode: InferenceMode = "llm",
    ) -> None:
        self._service = usage_assumptions_service or UsageAssumptionsService(
            ai_client=ai_client,
            inference_mode=inference_mode,
        )

    def infer_components(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
        inference_mode: InferenceMode | None = None,
    ) -> list[ComponentPricingInput]:
        return self._service.infer_components(
            project,
            components,
            feature_flags=feature_flags,
            inference_mode=inference_mode,
        )

    def infer_heuristic_fallback(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
    ) -> list[ComponentPricingInput]:
        return self._service.infer_components(
            project,
            components,
            feature_flags=feature_flags,
            inference_mode="heuristic",
        )

    @property
    def service(self) -> UsageAssumptionsService:
        return self._service
