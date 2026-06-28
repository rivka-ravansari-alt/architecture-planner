"""AWS catalog service references parsed from component catalog DB rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AwsAttributeFilter:
    field: str
    value: str
    match: str = "contains"

    @property
    def cache_key(self) -> tuple[str, str, str]:
        return (self.field.casefold(), self.match.casefold(), self.value.casefold())


@dataclass(frozen=True)
class AwsCatalogServiceRef:
    """One AWS billing target derived from architecture_components.aws_options."""

    name: str
    api_service_code: str
    attribute_filters: tuple[AwsAttributeFilter, ...] = ()
    region_code: str = "us-east-1"

    @property
    def mapping_key(self) -> tuple[str, str, tuple[tuple[str, str, str], ...]]:
        filter_key = tuple(f.cache_key for f in self.attribute_filters)
        return (self.api_service_code.casefold(), self.region_code.casefold(), filter_key)


def aws_option_display_name(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        return str(raw.get("name", "")).strip()
    return ""


def _parse_attribute_filters(raw_filters: Any) -> tuple[AwsAttributeFilter, ...]:
    if not isinstance(raw_filters, list):
        return ()

    filters: list[AwsAttributeFilter] = []
    for entry in raw_filters:
        if not isinstance(entry, dict):
            continue
        field = str(entry.get("field", "")).strip()
        value = str(entry.get("value", "")).strip()
        if not field or not value:
            continue
        match = str(entry.get("match", "contains")).strip() or "contains"
        filters.append(AwsAttributeFilter(field=field, value=value, match=match))
    return tuple(filters)


def parse_aws_catalog_option(raw: Any) -> AwsCatalogServiceRef | None:
    if isinstance(raw, str):
        name = raw.strip()
        if not name:
            return None
        return AwsCatalogServiceRef(name=name, api_service_code=name)

    if isinstance(raw, dict):
        name = str(raw.get("name", "")).strip()
        if not name:
            return None
        api_service_code = str(raw.get("api_service_code", name)).strip() or name
        region_code = str(raw.get("region_code", "us-east-1")).strip() or "us-east-1"
        return AwsCatalogServiceRef(
            name=name,
            api_service_code=api_service_code,
            attribute_filters=_parse_attribute_filters(raw.get("attribute_filters")),
            region_code=region_code,
        )

    return None
