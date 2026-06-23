"""Hardcoded component defaults keyed by component type."""

from __future__ import annotations

from app.config.params import (
    CLOUD_DEFAULTS_BY_TYPE,
    CLOUD_DEFAULTS_FALLBACK_TYPE,
    CLOUD_PROVIDERS,
    COMPONENT_TYPE_ALIASES,
    COMPONENT_TYPE_DESCRIPTIONS,
    DEFAULT_COMPONENT_TYPE,
)


class CloudDefaultsService:
    def default_cloud_options_for_type(self, component_type: str) -> dict[str, list[str]]:
        normalized = self._normalize_type(component_type)
        defaults = CLOUD_DEFAULTS_BY_TYPE.get(normalized) or CLOUD_DEFAULTS_BY_TYPE[
            CLOUD_DEFAULTS_FALLBACK_TYPE
        ]
        return {provider: list(defaults[provider]) for provider in CLOUD_PROVIDERS}

    def default_reason_for_type(self, component_type: str) -> str:
        normalized = self._normalize_type(component_type)
        description = COMPONENT_TYPE_DESCRIPTIONS.get(normalized)
        if description:
            return description
        label = normalized.replace("_", " ")
        return f"Provides {label} capabilities for this architecture."

    def normalize_cloud_options(self, component: dict) -> dict[str, list[str]]:
        component_type = str(component.get("type", DEFAULT_COMPONENT_TYPE)).strip().lower()
        return self.default_cloud_options_for_type(component_type)

    @staticmethod
    def _normalize_type(component_type: str) -> str:
        normalized = str(component_type).strip().lower()
        return COMPONENT_TYPE_ALIASES.get(normalized, normalized)
