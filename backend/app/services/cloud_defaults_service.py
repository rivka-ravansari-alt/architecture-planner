"""Default cloud service options when the AI omits provider lists."""

from __future__ import annotations

from app.config.params import (
    CLOUD_DEFAULTS_BY_TYPE,
    CLOUD_DEFAULTS_FALLBACK_TYPE,
    CLOUD_PROVIDER_ALIASES,
    CLOUD_PROVIDERS,
    DEFAULT_COMPONENT_TYPE,
)


class CloudDefaultsService:
    def default_cloud_options_for_type(self, component_type: str) -> dict[str, list[str]]:
        defaults = CLOUD_DEFAULTS_BY_TYPE.get(component_type) or CLOUD_DEFAULTS_BY_TYPE[
            CLOUD_DEFAULTS_FALLBACK_TYPE
        ]
        return {provider: list(defaults[provider]) for provider in CLOUD_PROVIDERS}

    def normalize_cloud_options(self, component: dict) -> dict[str, list[str]]:
        raw = component.get("cloud_options")
        cloud_options = raw if isinstance(raw, dict) else {}
        component_type = str(component.get("type", DEFAULT_COMPONENT_TYPE)).strip().lower()
        defaults = self.default_cloud_options_for_type(component_type)

        normalized: dict[str, list[str]] = {}
        for provider in CLOUD_PROVIDERS:
            options = self._options_for_provider(cloud_options, provider)
            cleaned = [str(option).strip() for option in options if str(option).strip()]
            normalized[provider] = cleaned or list(defaults[provider])
        return normalized

    def _options_for_provider(self, cloud_options: dict, provider: str) -> list:
        direct = cloud_options.get(provider)
        if isinstance(direct, list):
            return direct
        if isinstance(direct, str) and direct.strip():
            return [direct]

        for key, value in cloud_options.items():
            key_lower = str(key).strip().lower()
            if key_lower in CLOUD_PROVIDER_ALIASES[provider]:
                if isinstance(value, list):
                    return value
                if isinstance(value, str) and value.strip():
                    return [value]
        return []
