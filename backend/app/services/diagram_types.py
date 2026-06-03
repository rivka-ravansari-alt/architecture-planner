"""Canonical architecture diagram keys for AI generation and validation."""

from __future__ import annotations

DIAGRAM_KEYS: tuple[str, ...] = ("high_level", "system_flow", "technical_flow")

DEFAULT_DIAGRAM_TITLES: dict[str, str] = {
    "high_level": "High Level Architecture",
    "system_flow": "System Flow",
    "technical_flow": "Technical Flow",
}
