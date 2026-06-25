"""Diagram payload normalization helpers."""

from __future__ import annotations

from typing import Any

from app.config.params import LEGACY_DIAGRAM_KEY_ALIASES


def migrate_diagram_keys(diagrams: dict[str, Any]) -> dict[str, Any]:
    migrated = dict(diagrams)
    for legacy_key, current_key in LEGACY_DIAGRAM_KEY_ALIASES.items():
        if legacy_key in migrated and current_key not in migrated:
            migrated[current_key] = migrated.pop(legacy_key)
        elif legacy_key in migrated:
            migrated.pop(legacy_key, None)
    return migrated
