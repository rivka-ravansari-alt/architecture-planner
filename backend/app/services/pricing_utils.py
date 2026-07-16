"""Shared helpers for Step 4 pricing."""

from __future__ import annotations

from app.config.params import PRICING_SERVICE_DISPLAY_NAMES


def pricing_service_display_name(service_id: str) -> str:
    """Return a human-readable cloud service label."""

    if service_id in PRICING_SERVICE_DISPLAY_NAMES:
        return PRICING_SERVICE_DISPLAY_NAMES[service_id]

    parts = service_id.split("_")
    if not parts:
        return service_id

    provider_prefixes = {
        "aws": "AWS",
        "gcp": "Google Cloud",
        "azure": "Azure",
    }
    if parts[0] in provider_prefixes:
        provider = provider_prefixes[parts[0]]
        name = " ".join(part.capitalize() for part in parts[1:] if part)
        return f"{provider} {name}".strip()

    return " ".join(part.capitalize() for part in parts if part)


def format_service_type(service_type: str | None) -> str:
    """Format a mapping ``service_type`` slug for display."""

    if not service_type:
        return ""
    return service_type.replace("_", " ").title()
