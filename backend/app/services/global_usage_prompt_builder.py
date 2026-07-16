"""Builds the global usage model prompt (Step 3)."""

from __future__ import annotations

import json
from typing import Any

from app.config.params import GLOBAL_USAGE_MODEL_PROMPT, PLATFORM_LABELS, USAGE_PARAMETER_GUIDANCE


class GlobalUsagePromptBuilder:
    def build(
        self,
        *,
        application_description: str,
        platform: str,
        stage: str,
        expected_users: int,
        requirements: dict[str, Any],
        selected_components: list[dict[str, Any]],
        usage_parameters: list[str],
        static_usage_values: dict[str, Any] | None = None,
    ) -> str:
        platform_label = PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())
        replacements = {
            "{{application_description}}": application_description.strip(),
            "{{platform}}": platform_label,
            "{{stage}}": str(stage),
            "{{expected_users}}": str(expected_users),
            "{{requirements}}": self._format_requirements(requirements),
            "{{static_usage_values}}": self._format_static_usage_values(
                static_usage_values
            ),
            "{{selected_components}}": self._format_selected_components(
                selected_components
            ),
            "{{usage_parameters}}": self._format_usage_parameters(usage_parameters),
        }

        prompt = GLOBAL_USAGE_MODEL_PROMPT
        for token, value in replacements.items():
            prompt = prompt.replace(token, value)
        return prompt

    @staticmethod
    def _format_requirements(requirements: dict[str, Any]) -> str:
        if not requirements:
            return "No specific requirements were provided."
        return json.dumps(requirements, indent=2, sort_keys=True)

    @staticmethod
    def _format_static_usage_values(static_usage_values: dict[str, Any] | None) -> str:
        if not static_usage_values:
            return "None."
        return json.dumps(static_usage_values, indent=2, sort_keys=True)

    @staticmethod
    def _format_selected_components(selected_components: list[dict[str, Any]]) -> str:
        if not selected_components:
            return "No architecture components were selected."

        lines: list[str] = []
        for component in selected_components:
            category_id = component.get("category_id") or component.get("id", "")
            name = component.get("name", category_id)
            description = component.get("description", "")
            reason = component.get("reason", "")
            lines.append(
                f"- id: {category_id}\n"
                f"  name: {name}\n"
                f"  description: {description}\n"
                f"  reason: {reason}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_usage_parameters(usage_parameters: list[str]) -> str:
        if not usage_parameters:
            return "No usage parameters were requested."

        lines: list[str] = []
        for parameter in usage_parameters:
            guidance = USAGE_PARAMETER_GUIDANCE.get(parameter)
            if guidance:
                lines.append(f"- {parameter}: {guidance}")
            else:
                lines.append(f"- {parameter}")
        return "\n".join(lines)
