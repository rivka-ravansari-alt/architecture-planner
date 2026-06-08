"""Builds the architecture generation prompt from project inputs."""

from __future__ import annotations

from app.config.params import (
    PROMPT_ARCHITECTURE_TEMPLATE,
    PROMPT_COMPONENT_TYPE_LIST,
    PROMPT_STAGE_GUIDANCE_MVP,
    PROMPT_STAGE_GUIDANCE_PRODUCTION,
    REQUIREMENT_KEYS,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
)
from app.models import Project


class PromptBuilderService:
    def build(self, project: Project) -> str:
        answers_dict = self._build_answers_dict(project)
        requirement_lines = self._format_requirements(answers_dict)
        return self._assemble_prompt(project, requirement_lines)

    def _build_answers_dict(self, project: Project) -> dict[str, bool]:
        answers = project.answers
        return {key: getattr(answers, key, False) if answers else False for key in REQUIREMENT_KEYS}

    def _format_requirements(self, answers_dict: dict[str, bool]) -> list[str]:
        return [
            f"- {REQUIREMENT_LABELS[key]}: {self._yes_no(value)}"
            for key, value in answers_dict.items()
        ]

    def _assemble_prompt(
        self,
        project: Project,
        requirement_lines: list[str],
    ) -> str:
        stage_label = STAGE_LABELS.get(project.stage, project.stage)
        prompt = PROMPT_ARCHITECTURE_TEMPLATE.format(
            product_name=project.name,
            description=project.description or "(not provided)",
            stage_label=stage_label,
            requirement_lines="\n".join(requirement_lines),
            stage_guidance=self._stage_guidance(project.stage),
            component_type_list=PROMPT_COMPONENT_TYPE_LIST,
        )
        return prompt

    @staticmethod
    def _stage_guidance(stage: str) -> str:
        if stage == "production":
            return PROMPT_STAGE_GUIDANCE_PRODUCTION
        return PROMPT_STAGE_GUIDANCE_MVP

    @staticmethod
    def _yes_no(value: bool) -> str:
        return "Yes" if value else "No"
