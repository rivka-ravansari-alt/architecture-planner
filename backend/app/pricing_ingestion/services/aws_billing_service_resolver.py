"""Resolve AWS Price List offers using catalog DB references."""

from __future__ import annotations

from typing import Any

from app.pricing_ingestion.models.aws_catalog_ref import AwsCatalogServiceRef


class AwsBillingServiceResolver:
    def __init__(self, services: list[dict[str, Any]]) -> None:
        self._by_service_code = {
            str(service.get("serviceCode", "")).casefold(): service
            for service in services
            if service.get("serviceCode")
        }

    def resolve(self, catalog_service: AwsCatalogServiceRef) -> dict[str, Any] | None:
        service = self._by_service_code.get(catalog_service.api_service_code.casefold())
        if service is None:
            return None

        return {
            **service,
            "displayName": catalog_service.name,
            "catalogService": catalog_service,
        }
