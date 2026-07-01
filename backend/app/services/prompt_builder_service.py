"""Builds the architecture generation prompt from project inputs."""

from __future__ import annotations

from app.config.params import (
    APPLICATION_PLATFORM_LABELS,
    APPLICATION_PLATFORM_MOBILE,
    APPLICATION_PLATFORM_WEB,
    PROMPT_COMPONENTS_TEMPLATE,
    PROMPT_DIAGRAMS_TEMPLATE,
    PROMPT_STAGE_GUIDANCE_MVP,
    PROMPT_STAGE_GUIDANCE_PRODUCTION,
    PROJECT_TYPE_LABELS,
    REQUIREMENT_KEYS,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
)
from app.models import Project, ProjectComponent
from app.services.catalog_service import CatalogService
from app.services.usage_profile_formatter import format_usage_profile_section


class PromptBuilderService:
    def __init__(self, catalog_service: CatalogService) -> None:
        self._catalog = catalog_service

    def build_components(self, project: Project) -> str:
        requirement_lines = self._format_requirements(project)
        stage_label = STAGE_LABELS.get(project.stage, project.stage)
        platform_label = self._format_application_platform(project.project_types)
        component_type_list = self._catalog.prompt_component_type_list()
        component_catalog = self._catalog.prompt_component_catalog()
        return PROMPT_COMPONENTS_TEMPLATE.format(
            product_name=project.name,
            description=project.description or "(not provided)",
            platform_label=platform_label,
            stage_label=stage_label,
            requirement_lines=requirement_lines,
            stage_guidance=self._stage_guidance(project.stage),
            component_catalog=component_catalog,
            component_type_list=component_type_list,
        )

    def build_diagrams(self, project: Project, components: list[ProjectComponent]) -> str:
        stage_label = STAGE_LABELS.get(project.stage, project.stage)
        component_lines = self._format_components(components)
        return PROMPT_DIAGRAMS_TEMPLATE.format(
            product_name=project.name,
            description=project.description or "(not provided)",
            stage_label=stage_label,
            component_lines=component_lines,
        )

    def _format_requirements(self, project: Project) -> str:
        answers = project.answers
        usage_profile = answers.usage_profile if answers else None
        if usage_profile:
            return format_usage_profile_section(
                usage_profile,
                expected_users=project.expected_users,
            )

        answers_dict = {
            key: getattr(answers, key, False) if answers else False for key in REQUIREMENT_KEYS
        }
        return "\n".join(
            f"- {REQUIREMENT_LABELS[key]}: {self._yes_no(value)}"
            for key, value in answers_dict.items()
        )

    def _format_components(self, components: list[ProjectComponent]) -> str:
        if not components:
            return "- (no components)"
        lines: list[str] = []
        for component in components:
            tag = "optional" if component.optional else "required"
            lines.append(
                f"- {component.name} (type: {component.component_type}, tag: {tag}): "
                f"{component.reason or '(no description)'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _stage_guidance(stage: str) -> str:
        if stage == "production":
            return PROMPT_STAGE_GUIDANCE_PRODUCTION
        return PROMPT_STAGE_GUIDANCE_MVP

    @staticmethod
    def _format_application_platform(project_types: list[str] | None) -> str:
        types = set(project_types or [])
        has_web = APPLICATION_PLATFORM_WEB in types
        has_mobile = APPLICATION_PLATFORM_MOBILE in types
        if has_web and has_mobile:
            return APPLICATION_PLATFORM_LABELS["both"]
        if has_mobile:
            return APPLICATION_PLATFORM_LABELS["mobile"]
        if has_web:
            return APPLICATION_PLATFORM_LABELS["web"]
        other = [PROJECT_TYPE_LABELS.get(project_type, project_type) for project_type in sorted(types)]
        return ", ".join(other) if other else "(not specified)"

    @staticmethod
    def _yes_no(value: bool) -> str:
        return "Yes" if value else "No"
