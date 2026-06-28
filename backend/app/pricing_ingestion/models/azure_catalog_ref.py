"""Azure catalog service references parsed from component catalog DB rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AzureCatalogServiceRef:
    """One Azure billing target derived from architecture_components.azure_options."""

    name: str
    api_service_name: str
    price_filter: str | None = None

    @property
    def mapping_key(self) -> tuple[str, str | None]:
        return (self.api_service_name.casefold(), self.price_filter)


def azure_option_display_name(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        return str(raw.get("name", "")).strip()
    return ""


def parse_azure_catalog_option(raw: Any) -> AzureCatalogServiceRef | None:
    if isinstance(raw, str):
        name = raw.strip()
        if not name:
            return None
        return AzureCatalogServiceRef(name=name, api_service_name=name)

    if isinstance(raw, dict):
        name = str(raw.get("name", "")).strip()
        if not name:
            return None
        api_service_name = str(raw.get("api_service_name", name)).strip() or name
        price_filter = raw.get("price_filter")
        if price_filter is not None:
            price_filter = str(price_filter).strip() or None
        return AzureCatalogServiceRef(
            name=name,
            api_service_name=api_service_name,
            price_filter=price_filter,
        )

    return None
