"""LLM-based Azure usage assumption inference (compatibility shim)."""

from __future__ import annotations

from app.clients.ai_client import BaseAIClient
from app.models import Project
from app.pricing.schemas import ComponentPricingInput
from app.pricing.usage.inference.llm.provider import LLMUsageInferenceProvider
from app.pricing.usage.service import UsageAssumptionsService
from app.schemas.domain import MappedComponent


class LLMUsageInferenceEngine:
    """Backward-compatible wrapper around UsageAssumptionsService."""

    def __init__(
        self,
        *,
        ai_client: BaseAIClient,
        service: UsageAssumptionsService | None = None,
    ) -> None:
        self._service = service or UsageAssumptionsService(ai_client=ai_client)
        self._llm = (
            self._service._primary
            if isinstance(self._service._primary, LLMUsageInferenceProvider)
            else LLMUsageInferenceProvider(ai_client=ai_client)
        )

    @property
    def heuristic(self):
        return self._service.fallback

    def build_prompt(self, project: Project, components: list[MappedComponent]) -> str:
        return self._service.build_prompt(project, components)

    def parse_response(
        self,
        raw: str,
        components: list[MappedComponent],
    ) -> list[ComponentPricingInput]:
        raise TypeError(
            "parse_response requires project context; use UsageAssumptionsService.parse_response."
        )

    def infer_components(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
    ) -> tuple[list[ComponentPricingInput], str, str | None]:
        result = self._service.infer(
            project,
            components,
            feature_flags=feature_flags,
            inference_mode="llm",
        )
        return (
            list(result.components),
            result.audit.prompt or "",
            result.audit.raw_response,
        )

    @staticmethod
    def system_prompt() -> str:
        return LLMUsageInferenceProvider.system_prompt()
