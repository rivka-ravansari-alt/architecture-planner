"""Resolve Azure Retail Prices services using catalog DB references."""

from __future__ import annotations

from typing import Any

from app.pricing_ingestion.models.azure_catalog_ref import AzureCatalogServiceRef


class AzureBillingServiceResolver:
    def __init__(self, services: list[dict[str, Any]]) -> None:
        self._by_api_service_name = {
            str(service.get("serviceName", "")).casefold(): service
            for service in services
            if service.get("serviceName")
        }

    def resolve(self, catalog_service: AzureCatalogServiceRef) -> dict[str, Any] | None:
        service = self._by_api_service_name.get(catalog_service.api_service_name.casefold())
        if service is None:
            return None

        return {
            **service,
            "displayName": catalog_service.name,
            "catalogService": catalog_service,
        }
