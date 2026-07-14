"""Builds the architecture component selection prompt (Step 2).

The category list is always injected from data loaded out of Firestore — no
category ids, names, descriptions, or types are hardcoded here.
"""

from __future__ import annotations

import json
from typing import Any

from app.config.params import PROMPT_COMPONENT_SELECTION_TEMPLATE


class ComponentSelectionPromptBuilder:
    def build(
        self,
        *,
        application_description: str,
        stage: str,
        expected_users: int,
        requirements: dict[str, Any],
        categories: list[dict[str, Any]],
    ) -> str:
        """Render the prompt template with the collected input and categories."""

        replacements = {
            "{{application_description}}": application_description.strip(),
            "{{stage}}": str(stage),
            "{{expected_users}}": str(expected_users),
            "{{requirements}}": self._format_requirements(requirements),
            "{{architecture_categories}}": self._format_categories(categories),
            "{{category_count}}": str(len(categories)),
        }

        prompt = PROMPT_COMPONENT_SELECTION_TEMPLATE
        for token, value in replacements.items():
            prompt = prompt.replace(token, value)
        return prompt

    @staticmethod
    def _format_requirements(requirements: dict[str, Any]) -> str:
        if not requirements:
            return "No specific requirements were provided."
        return json.dumps(requirements, indent=2, sort_keys=True)

    @staticmethod
    def _format_categories(categories: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for category in categories:
            category_id = category.get("id", "")
            name = category.get("name", category_id)
            description = category.get("description", "")
            lines.append(f"- id: {category_id}\n  name: {name}\n  description: {description}")
        return "\n".join(lines)
