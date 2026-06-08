"""Maps validated AI JSON to internal component models."""

from __future__ import annotations

import re
from typing import Any

from app.config.params import (
    CLOUD_PROVIDERS,
    COMPONENT_CATEGORY_CORE,
    COMPONENT_CATEGORY_OPTIONAL,
    COMPONENT_KEY_HINTS,
    COMPONENT_ORDER_MULTIPLIER,
    COMPONENT_TYPE_ALIASES,
    COMPONENT_TYPE_KEY_MAP,
    DEFAULT_COMPONENT_TYPE,
    SLUG_MAX_LENGTH,
    VALID_COMPONENT_TYPES,
)
from app.schemas.domain import MappedComponent


class ComponentMapperService:
    def map_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[list[MappedComponent], str, list[str]]:
        components = self._map_components(payload["components"])
        summary = str(payload["architecture"]["summary"]).strip()
        main_flow = [str(step).strip() for step in payload["architecture"]["flow"]]
        return components, summary, main_flow

    def feature_flags_from_components(self, components: list[MappedComponent]) -> dict[str, bool]:
        keys = {component.key for component in components if not component.optional}
        return {
            "file_upload": "object_storage" in keys,
            "ai": "ai_service" in keys or "ai_provider" in keys,
            "background_processing": "queue_worker" in keys or "queue" in keys,
        }

    def _map_components(self, items: list[dict[str, Any]]) -> list[MappedComponent]:
        used_keys: set[str] = set()
        components: list[MappedComponent] = []
        for order, item in enumerate(items):
            components.append(self._map_single_component(item, order, used_keys))
        return components

    def _map_single_component(
        self,
        item: dict[str, Any],
        order: int,
        used_keys: set[str],
    ) -> MappedComponent:
        name = str(item["name"]).strip()
        reason = str(item["reason"]).strip()
        optional = str(item["tag"]).strip().lower() == "optional"
        component_type = self._resolve_component_type(item)
        key = self.infer_component_key(name, used_keys, component_type)
        used_keys.add(key)
        cloud = self._extract_cloud_options(item["cloud_options"])
        implementation_options = self._extract_implementation_options(item.get("implementation_options"))
        return MappedComponent(
            key=key,
            name=name,
            component_type=component_type,
            reason=reason,
            category=COMPONENT_CATEGORY_OPTIONAL if optional else COMPONENT_CATEGORY_CORE,
            optional=optional,
            order=order * COMPONENT_ORDER_MULTIPLIER,
            cloud=cloud,
            implementation_options=implementation_options,
        )

    def _resolve_component_type(self, item: dict[str, Any]) -> str:
        component_type = str(item.get("type", DEFAULT_COMPONENT_TYPE)).strip().lower()
        component_type = COMPONENT_TYPE_ALIASES.get(component_type, component_type)
        if component_type not in VALID_COMPONENT_TYPES:
            return DEFAULT_COMPONENT_TYPE
        return component_type

    def _extract_cloud_options(self, cloud_options: dict) -> dict[str, list[str]]:
        return {
            provider: [
                str(option).strip()
                for option in cloud_options.get(provider, [])
                if str(option).strip()
            ]
            for provider in CLOUD_PROVIDERS
        }

    @staticmethod
    def _extract_implementation_options(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            field = str(key).strip()
            if not field:
                continue
            if field == "recommended":
                normalized[field] = str(item).strip().lower()
            elif isinstance(item, dict):
                normalized[field] = item
            else:
                text = str(item).strip()
                if text:
                    normalized[field] = text
        return normalized

    def infer_component_key(
        self,
        name: str,
        used_keys: set[str],
        component_type: str | None = None,
    ) -> str:
        if component_type and component_type in VALID_COMPONENT_TYPES:
            mapped = COMPONENT_TYPE_KEY_MAP.get(component_type)
            if mapped and mapped not in used_keys:
                return mapped
        lower = name.lower()
        for key, hints in COMPONENT_KEY_HINTS:
            if any(hint in lower for hint in hints) and key not in used_keys:
                return key
        return self._unique_slug(name, used_keys)

    def _unique_slug(self, name: str, used_keys: set[str]) -> str:
        base = self._slugify(name)
        candidate = base
        suffix = 2
        while candidate in used_keys:
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        return slug[:SLUG_MAX_LENGTH] or "component"
