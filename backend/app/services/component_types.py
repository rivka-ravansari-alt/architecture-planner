"""Canonical architecture component types returned by the AI."""

from __future__ import annotations

VALID_COMPONENT_TYPES = frozenset(
    {
        "user",
        "web_app",
        "mobile_app",
        "browser_extension",
        "api",
        "authentication",
        "database",
        "object_storage",
        "queue",
        "worker",
        "ai_service",
        "monitoring",
        "analytics",
        "notification",
        "payment",
    }
)

DEFAULT_COMPONENT_TYPE = "api"
