"""Normalize component catalog cloud options for API responses."""

from __future__ import annotations

from typing import Any

from app.pricing_ingestion.models.aws_catalog_ref import aws_option_display_name
from app.pricing_ingestion.models.azure_catalog_ref import azure_option_display_name


def cloud_option_display_name(provider: str, option: Any) -> str:
    if provider == "aws":
        return aws_option_display_name(option)
    if provider == "azure":
        return azure_option_display_name(option)
    return str(option).strip()


def cloud_options_as_strings(provider: str, options: Any) -> list[str]:
    if not isinstance(options, list):
        return []

    names: list[str] = []
    seen: set[str] = set()
    for option in options:
        name = cloud_option_display_name(provider, option)
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names
