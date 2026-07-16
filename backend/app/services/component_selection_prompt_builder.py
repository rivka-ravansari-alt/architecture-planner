"""Builds the architecture component selection prompt (Step 2).

The category list is always injected from data loaded out of Firestore — no
category ids, names, descriptions, or types are hardcoded here.
"""

from __future__ import annotations

from typing import Any

from app.config.params import (
    INTAKE_REQUIREMENT_LABELS,
    PLATFORM_LABELS,
    PROMPT_COMPONENT_SELECTION_TEMPLATE,
)


class ComponentSelectionPromptBuilder:
    def build(
        self,
        *,
        application_description: str,
        platform: str,
        stage: str,
        expected_users: int,
        requirements: dict[str, Any],
        categories: list[dict[str, Any]],
    ) -> str:
        """Render the prompt template with the collected input and categories."""

        category_ids = [category.get("id", "") for category in categories if category.get("id")]
        platform_label = PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())
        replacements = {
            "{{application_description}}": application_description.strip(),
            "{{platform}}": platform_label,
            "{{stage}}": str(stage),
            "{{expected_users}}": str(expected_users),
            "{{requirements}}": self._format_requirements(requirements),
            "{{architecture_categories}}": self._format_categories(categories),
            "{{category_count}}": str(len(categories)),
            "{{valid_category_ids}}": ", ".join(category_ids),
        }

        prompt = PROMPT_COMPONENT_SELECTION_TEMPLATE
        for token, value in replacements.items():
            prompt = prompt.replace(token, value)
        return prompt

    @staticmethod
    def _format_requirements(requirements: dict[str, Any]) -> str:
        if not requirements:
            return "No specific requirements were provided."

        lines: list[str] = []
        for key in sorted(requirements):
            value = requirements[key]
            if not isinstance(value, dict):
                continue

            label = INTAKE_REQUIREMENT_LABELS.get(key, key.replace("_", " ").title())
            if not value.get("enabled"):
                lines.append(f"- {label}: not required")
                continue

            details: list[str] = []
            for field_key, field_value in sorted(value.items()):
                if field_key == "enabled":
                    continue
                if field_value in ("", None, [], {}):
                    continue
                if isinstance(field_value, list):
                    rendered = ", ".join(str(item) for item in field_value)
                    details.append(f"{field_key.replace('_', ' ')}: {rendered}")
                else:
                    details.append(f"{field_key.replace('_', ' ')}: {field_value}")

            if details:
                lines.append(f"- {label}: required ({'; '.join(details)})")
            else:
                lines.append(f"- {label}: required")

        return "\n".join(lines) if lines else "No specific requirements were provided."

    @staticmethod
    def _format_categories(categories: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for category in categories:
            category_id = category.get("id", "")
            name = category.get("name", category_id)
            description = category.get("description", "")
            lines.append(f"- id: {category_id}\n  name: {name}\n  description: {description}")
        return "\n".join(lines)
