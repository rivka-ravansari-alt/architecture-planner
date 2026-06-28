"""Azure Retail Prices API client (no authentication required)."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx

from app.config.settings import settings
from app.core.exceptions import ServiceUnavailableError
from app.pricing_ingestion.models.azure_catalog_ref import AzureCatalogServiceRef
from app.pricing_ingestion.providers.base import BillingClient

_AZURE_API_VERSION = "2023-01-01-preview"
_DEFAULT_CURRENCY = "USD"
_CONSUMPTION_FILTER = "priceType eq 'Consumption'"
_MAX_RETRIES = 6
_RETRY_BASE_SECONDS = 5.0


class AzureBillingClient(BillingClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._base_url = (base_url or settings.azure_billing_base_url).rstrip("/")
        self._timeout = timeout_seconds

    def list_services(self, catalog_services: list[AzureCatalogServiceRef] | None = None) -> list[dict[str, Any]]:
        """Return Azure Retail Prices service metadata for the given catalog services."""
        services: dict[str, dict[str, Any]] = {}
        seen_mapping_keys: set[tuple[str, str | None]] = set()

        for ref in catalog_services or []:
            if ref.mapping_key in seen_mapping_keys:
                continue
            seen_mapping_keys.add(ref.mapping_key)

            items = self._fetch_prices(ref, max_items=1)
            if not items:
                continue

            item = items[0]
            service_id = str(item.get("serviceId", ""))
            if not service_id or service_id in services:
                continue

            services[service_id] = {
                "serviceId": service_id,
                "serviceName": str(item.get("serviceName", ref.api_service_name)),
                "displayName": ref.name,
            }

        return list(services.values())

    def list_skus_for_service(
        self,
        service_id: str,
        *,
        catalog_service: AzureCatalogServiceRef | None = None,
        catalog_name: str | None = None,
    ) -> list[dict[str, Any]]:
        del service_id
        if catalog_service is None:
            if not catalog_name:
                return []
            catalog_service = AzureCatalogServiceRef(
                name=catalog_name,
                api_service_name=catalog_name,
            )
        return self._fetch_prices(catalog_service)

    def _fetch_prices(
        self,
        ref: AzureCatalogServiceRef,
        *,
        max_items: int | None = None,
    ) -> list[dict[str, Any]]:
        filter_expr = self._build_filter(ref)
        return self._paginate(filter_expr, max_items=max_items)

    @staticmethod
    def _build_filter(ref: AzureCatalogServiceRef) -> str:
        escaped_name = ref.api_service_name.replace("'", "''")
        parts = [
            f"serviceName eq '{escaped_name}'",
            _CONSUMPTION_FILTER,
        ]
        if ref.price_filter:
            parts.append(ref.price_filter)
        return " and ".join(parts)

    def _paginate(self, filter_expr: str, *, max_items: int | None = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        url: str | None = self._initial_url(filter_expr)

        while url:
            payload = self._get(url)
            batch = payload.get("Items") or []
            if not isinstance(batch, list):
                raise ServiceUnavailableError("Azure Retail Prices API returned an unexpected response.")

            items.extend(batch)
            if max_items is not None and len(items) >= max_items:
                return items[:max_items]

            next_link = payload.get("NextPageLink")
            url = str(next_link) if next_link else None

        return items

    def _initial_url(self, filter_expr: str) -> str:
        return (
            f"{self._base_url}?api-version={quote(_AZURE_API_VERSION)}"
            f"&currencyCode={quote(_DEFAULT_CURRENCY)}"
            f"&$filter={quote(filter_expr, safe='')}"
        )

    def _get(self, url: str) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = httpx.get(url, timeout=self._timeout)
                if response.status_code == 429:
                    wait_seconds = _RETRY_BASE_SECONDS * (attempt + 1)
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_seconds = max(wait_seconds, float(retry_after))
                    time.sleep(wait_seconds)
                    continue
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                last_error = ServiceUnavailableError(
                    "Azure Retail Prices API request failed "
                    f"({exc.response.status_code}): {exc.response.text}"
                )
                break
            except httpx.HTTPError as exc:
                last_error = ServiceUnavailableError(
                    f"Azure Retail Prices API request failed: {exc}"
                )
                break
            else:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ServiceUnavailableError(
                        "Azure Retail Prices API returned an unexpected response."
                    )
                return payload

        if last_error is not None:
            raise last_error
        raise ServiceUnavailableError("Azure Retail Prices API rate limit exceeded after retries.")
