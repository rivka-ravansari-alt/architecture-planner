"""Shared component type helpers."""

from __future__ import annotations

from app.config.params import COMPONENT_TYPE_ALIASES


def normalize_component_type(component_type: str) -> str:
    normalized = str(component_type or "").strip().lower()
    return COMPONENT_TYPE_ALIASES.get(normalized, normalized)
