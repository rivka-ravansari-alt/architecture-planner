"""AWS Price List Bulk API client (no authentication required)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config.settings import settings
from app.core.exceptions import ServiceUnavailableError
from app.pricing_ingestion.models.aws_catalog_ref import AwsCatalogServiceRef
from app.pricing_ingestion.providers.base import BillingClient

_MAX_RETRIES = 6
_RETRY_BASE_SECONDS = 5.0
_DEFAULT_TIMEOUT_SECONDS = 180.0


class AwsBillingClient(BillingClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = (base_url or settings.aws_pricing_bulk_base_url).rstrip("/")
        self._timeout = timeout_seconds
        self._aws_index: dict[str, Any] | None = None
        self._offer_cache: dict[str, dict[str, Any]] = {}

    def list_services(
        self,
        catalog_services: list[AwsCatalogServiceRef] | None = None,
    ) -> list[dict[str, Any]]:
        """Return AWS offer metadata for catalog-referenced service codes."""
        services: list[dict[str, Any]] = []
        seen_codes: set[str] = set()

        for ref in catalog_services or []:
            code = ref.api_service_code
            code_key = code.casefold()
            if code_key in seen_codes:
                continue
            if self._find_offer_key(code) is None:
                continue

            seen_codes.add(code_key)
            services.append(
                {
                    "serviceId": code,
                    "serviceCode": code,
                    "displayName": ref.name,
                }
            )

        return services

    def list_skus_for_service(
        self,
        service_id: str,
        *,
        catalog_service: AwsCatalogServiceRef | None = None,
    ) -> list[dict[str, Any]]:
        ref = catalog_service or AwsCatalogServiceRef(
            name=service_id,
            api_service_code=service_id,
        )
        offer = self._load_offer(ref.api_service_code)
        return self._collect_priced_products(offer, ref)

    def _collect_priced_products(
        self,
        offer: dict[str, Any],
        ref: AwsCatalogServiceRef,
    ) -> list[dict[str, Any]]:
        products = offer.get("products") or {}
        on_demand = (offer.get("terms") or {}).get("OnDemand") or {}
        priced: list[dict[str, Any]] = []

        for sku, product in products.items():
            attributes = product.get("attributes") or {}
            if str(attributes.get("regionCode", "")).casefold() != ref.region_code.casefold():
                continue
            if not self._matches_attribute_filters(attributes, ref):
                continue

            term = self._select_on_demand_term(on_demand.get(sku))
            if term is None:
                continue

            price_dimension = self._select_price_dimension(term)
            if price_dimension is None:
                continue

            priced.append(
                {
                    "sku": sku,
                    "productFamily": product.get("productFamily", ""),
                    "attributes": attributes,
                    "priceDimension": price_dimension,
                    "effectiveDate": term.get("effectiveDate"),
                }
            )

        return priced

    @staticmethod
    def _matches_attribute_filters(
        attributes: dict[str, Any],
        ref: AwsCatalogServiceRef,
    ) -> bool:
        for attribute_filter in ref.attribute_filters:
            value = str(attributes.get(attribute_filter.field, ""))
            if attribute_filter.match == "equals":
                if value != attribute_filter.value:
                    return False
            elif attribute_filter.value.casefold() not in value.casefold():
                return False
        return True

    @staticmethod
    def _select_on_demand_term(terms_for_sku: Any) -> dict[str, Any] | None:
        if not isinstance(terms_for_sku, dict) or not terms_for_sku:
            return None
        return max(
            terms_for_sku.values(),
            key=lambda term: str(term.get("effectiveDate", "")),
        )

    @staticmethod
    def _select_price_dimension(term: dict[str, Any]) -> dict[str, Any] | None:
        dimensions = term.get("priceDimensions") or {}
        if not isinstance(dimensions, dict) or not dimensions:
            return None
        return next(iter(dimensions.values()))

    def _load_aws_index(self) -> dict[str, Any]:
        if self._aws_index is None:
            self._aws_index = self._get_json("/offers/v1.0/aws/index.json")
        return self._aws_index

    def _find_offer_key(self, service_code: str) -> str | None:
        offers = self._load_aws_index().get("offers", {})
        if service_code in offers:
            return service_code

        for key, metadata in offers.items():
            if str(metadata.get("offerCode", "")).casefold() == service_code.casefold():
                return key

        for key in offers:
            if key.casefold() == service_code.casefold():
                return key
        return None

    def _load_offer(self, service_code: str) -> dict[str, Any]:
        cached = self._offer_cache.get(service_code)
        if cached is not None:
            return cached

        offer = self._get_json(f"/offers/v1.0/aws/{service_code}/current/index.json")
        self._offer_cache[service_code] = offer
        return offer

    def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = httpx.get(url, timeout=self._timeout)
                if response.status_code == 429:
                    time.sleep(_RETRY_BASE_SECONDS * (attempt + 1))
                    continue
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    raise ServiceUnavailableError(
                        f"AWS price list offer not found for path '{path}'."
                    ) from exc
                last_error = ServiceUnavailableError(
                    f"AWS Price List API request failed ({exc.response.status_code}): "
                    f"{exc.response.text}"
                )
                break
            except httpx.HTTPError as exc:
                last_error = ServiceUnavailableError(f"AWS Price List API request failed: {exc}")
                break
            else:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ServiceUnavailableError("AWS Price List API returned an unexpected response.")
                return payload

        if last_error is not None:
            raise last_error
        raise ServiceUnavailableError("AWS Price List API rate limit exceeded after retries.")
