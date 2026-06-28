"""Component defaults loaded from the component catalog."""

from __future__ import annotations

from app.config.params import (
    CLOUD_DEFAULTS_FALLBACK_TYPE,
    CLOUD_PROVIDERS,
    DEFAULT_COMPONENT_TYPE,
)
from app.models.component_catalog import ComponentCatalog
from app.pricing_ingestion.models.aws_catalog_ref import aws_option_display_name
from app.pricing_ingestion.models.azure_catalog_ref import azure_option_display_name
from app.repositories.component_catalog_repository import ComponentCatalogRepository
from app.utils.component_type import normalize_component_type


class CloudDefaultsService:
    def __init__(self, catalog_repo: ComponentCatalogRepository) -> None:
        self._catalog_repo = catalog_repo

    def default_cloud_options_for_type(self, component_type: str) -> dict[str, list[str]]:
        normalized = self._normalize_type(component_type)
        entry = self._find_catalog_entry(normalized)
        if entry is None:
            fallback = self._find_catalog_entry(CLOUD_DEFAULTS_FALLBACK_TYPE)
            entry = fallback
        if entry is None:
            return {provider: [] for provider in CLOUD_PROVIDERS}
        return {
            "aws": [
                aws_option_display_name(option)
                for option in entry.aws_options
                if aws_option_display_name(option)
            ],
            "gcp": list(entry.gcp_options),
            "azure": [
                azure_option_display_name(option)
                for option in entry.azure_options
                if azure_option_display_name(option)
            ],
        }

    def default_reason_for_type(self, component_type: str) -> str:
        normalized = self._normalize_type(component_type)
        entry = self._find_catalog_entry(normalized)
        if entry and entry.description:
            return entry.description
        label = normalized.replace("_", " ")
        return f"Provides {label} capabilities for this architecture."

    def normalize_cloud_options(self, component: dict) -> dict[str, list[str]]:
        component_type = normalize_component_type(
            str(component.get("type", DEFAULT_COMPONENT_TYPE))
        )
        return self.default_cloud_options_for_type(component_type)

    def _find_catalog_entry(self, component_type: str) -> ComponentCatalog | None:
        return self._catalog_repo.find_by_name(component_type)

    def _normalize_type(self, component_type: str) -> str:
        return normalize_component_type(component_type)
