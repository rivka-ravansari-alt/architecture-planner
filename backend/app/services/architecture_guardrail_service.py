"""Post-AI guardrails for component tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import Project


@dataclass(frozen=True)
class GuardrailContext:
    dashboards: bool

    @classmethod
    def from_project(cls, project: Project) -> GuardrailContext:
        answers = project.answers
        return cls(dashboards=bool(answers and answers.dashboards))


class ArchitectureGuardrailService:
    def apply(self, payload: dict[str, Any], project: Project) -> dict[str, Any]:
        context = GuardrailContext.from_project(project)
        components = payload.get("components")
        if not isinstance(components, list):
            return payload

        for component in components:
            if not isinstance(component, dict):
                continue
            self._apply_component_tag_guardrails(component, context)

        return payload

    def _apply_component_tag_guardrails(
        self,
        component: dict[str, Any],
        context: GuardrailContext,
    ) -> None:
        component_type = str(component.get("type", "")).strip().lower()
        if component_type != "analytics":
            return
        if context.dashboards:
            return
        if str(component.get("tag", "")).strip().lower() != "required":
            return
        component["tag"] = "optional"
