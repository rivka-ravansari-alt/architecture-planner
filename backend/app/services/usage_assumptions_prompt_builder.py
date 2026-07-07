"""Build LLM prompts for usage assumption inference (compatibility shim)."""

from __future__ import annotations

from app.models import Project
from app.pricing.usage.context_builder import UsageContextBuilder
from app.pricing.usage.inference.llm.prompt_builder import LLMUsageAssumptionsPromptBuilder
from app.schemas.domain import MappedComponent


class UsageAssumptionsPromptBuilder:
    """Backward-compatible prompt builder accepting Project + components."""

    def __init__(self) -> None:
        self._builder = LLMUsageAssumptionsPromptBuilder()
        self._context_builder = UsageContextBuilder()

    def build(self, project: Project, components: list[MappedComponent]) -> str:
        context = self._context_builder.build(project, components)
        return self._builder.build(context)


__all__ = ["UsageAssumptionsPromptBuilder"]
