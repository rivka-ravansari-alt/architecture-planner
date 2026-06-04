"""Builds the architecture generation prompt from project inputs."""

from __future__ import annotations

from app.config.params import (
    EXPECTED_USERS_LABELS,
    PROJECT_TYPE_LABELS,
    PROMPT_COMPONENT_TYPE_LIST,
    PROMPT_JSON_EXAMPLE,
    REQUIREMENT_KEYS,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
)
from app.models import Project


class PromptBuilderService:
    """Constructs the LLM prompt from a project's wizard answers."""

    def build(self, project: Project) -> str:
        answers_dict = self._build_answers_dict(project)
        type_labels = self._format_project_types(project)
        requirement_lines = self._format_requirements(answers_dict)
        return self._assemble_prompt(project, type_labels, requirement_lines)

    def _build_answers_dict(self, project: Project) -> dict[str, bool]:
        answers = project.answers
        return {key: getattr(answers, key, False) if answers else False for key in REQUIREMENT_KEYS}

    def _format_project_types(self, project: Project) -> list[str]:
        return [
            PROJECT_TYPE_LABELS.get(project_type, project_type.replace("_", " ").title())
            for project_type in (project.project_types or [])
        ]

    def _format_requirements(self, answers_dict: dict[str, bool]) -> list[str]:
        return [
            f"- {REQUIREMENT_LABELS[key]}: {self._yes_no(value)}"
            for key, value in answers_dict.items()
        ]

    def _assemble_prompt(
        self,
        project: Project,
        type_labels: list[str],
        requirement_lines: list[str],
    ) -> str:
        stage_label = STAGE_LABELS.get(project.stage, project.stage)
        users_label = EXPECTED_USERS_LABELS.get(project.expected_users, project.expected_users)
        description = project.description or "(not provided)"

        return f"""You are a senior software architect. Design a technology-agnostic architecture plan for the product described below.

Respond with JSON only. Do not include markdown, code fences, or any text outside the JSON object.

## Product

- Product name: {project.name}
- Product description: {description}
- Project type(s): {", ".join(type_labels)}
- Stage: {stage_label}
- Expected users: {users_label}

## Requirements

{chr(10).join(requirement_lines)}

## Instructions

1. Propose concrete architecture components that fit the product, stage, and requirements.
2. Assign each component a type from this list only (do not invent icons or other visual metadata):
   {PROMPT_COMPONENT_TYPE_LIST}
3. Mark each component tag as "required" or "optional".
4. Explain why each component is needed in the reason field.
5. For each component, include cloud_options with keys aws, gcp, and azure — each must be a non-empty array of concrete service names. For type "user", use "N/A — not a managed cloud service" on every provider. Never leave a provider list empty.
6. Provide a high-level architecture summary and a step-by-step flow.
7. Provide three complementary diagrams under diagrams — each with title, nodes, and edges. Node ids must be unique within each diagram. Prefer matching component names where applicable.
   - high_level (title: "High Level Design"): Business and system-boundary view. Optional node field "group" with values: experience, platform, data, operations.
   - system_flow (title: "System Flow"): Request and data movement through the system.
   - technical_flow (title: "Technical Flow"): Internal implementation detail with infrastructure at the bottom.
8. Identify risks with severity low, medium, or high.
9. Provide actionable recommendations and next steps.

## Required JSON shape

{PROMPT_JSON_EXAMPLE}
"""

    @staticmethod
    def _yes_no(value: bool) -> str:
        return "Yes" if value else "No"
