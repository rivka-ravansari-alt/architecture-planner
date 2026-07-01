"""Safe predefined unit conversions for pricing profile billable SKUs."""

from __future__ import annotations

_SECONDS_PER_HOUR = 3600.0

SUPPORTED_CONVERSIONS = frozenset(
    {
        "none",
        "per_thousand",
        "per_million",
        "seconds_to_hours",
        "gib_seconds_to_gib_hours",
        "gb_month",
        "tokens_per_1k",
        "tokens_per_1m",
    }
)


class UnsupportedConversionError(ValueError):
    """Raised when a pricing profile references an unknown conversion."""


def apply_conversion(raw_value: float, conversion: str) -> tuple[float, str]:
    """Return (quantity, human-readable note) for a raw usage metric value."""
    normalized = conversion.strip().casefold()
    if normalized not in SUPPORTED_CONVERSIONS:
        raise UnsupportedConversionError(f"Unsupported conversion '{conversion}'")

    if normalized == "none" or normalized == "gb_month":
        return raw_value, f"{raw_value}"

    if normalized == "per_thousand":
        quantity = raw_value / 1_000
        return quantity, f"{raw_value} / 1_000"

    if normalized == "per_million":
        quantity = raw_value / 1_000_000
        return quantity, f"{raw_value} / 1_000_000"

    if normalized == "seconds_to_hours":
        quantity = raw_value / _SECONDS_PER_HOUR
        return quantity, f"{raw_value} / 3600 -> hours"

    if normalized == "gib_seconds_to_gib_hours":
        quantity = raw_value / _SECONDS_PER_HOUR
        return quantity, f"{raw_value} / 3600 -> gib-hours"

    if normalized == "tokens_per_1k":
        quantity = raw_value / 1_000
        return quantity, f"{raw_value} / 1_000"

    if normalized == "tokens_per_1m":
        quantity = raw_value / 1_000_000
        return quantity, f"{raw_value} / 1_000_000"

    raise UnsupportedConversionError(f"Unsupported conversion '{conversion}'")
