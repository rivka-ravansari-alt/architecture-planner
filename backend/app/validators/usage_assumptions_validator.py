"""Validate LLM usage-assumption responses (compatibility shim)."""

from __future__ import annotations

from app.models import Project
from app.pricing.schemas import ComponentPricingInput
from app.pricing.usage.context_builder import UsageContextBuilder
from app.pricing.usage.inference.llm.response_validator import (
    LLMUsageAssumptionsResponseValidator,
)
from app.schemas.domain import MappedComponent


class UsageAssumptionsValidator:
    """Backward-compatible validator accepting Project + components."""

    def __init__(self) -> None:
        self._validator = LLMUsageAssumptionsResponseValidator()
        self._context_builder = UsageContextBuilder()

    def validate(
        self,
        raw: str,
        components: list[MappedComponent],
        *,
        project: Project | None = None,
        feature_flags: dict[str, bool] | None = None,
    ) -> list[ComponentPricingInput]:
        if project is None:
            raise ValueError("project is required for usage assumption validation")
        context = self._context_builder.build(
            project,
            components,
            feature_flags=feature_flags,
        )
        result = self._validator.validate(raw, context)
        return list(result.components)
