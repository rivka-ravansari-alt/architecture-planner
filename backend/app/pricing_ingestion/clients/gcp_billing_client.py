"""Google Cloud Billing Catalog API client (ADC authentication)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config.settings import settings
from app.core.exceptions import ServiceUnavailableError
from app.pricing_ingestion.providers.base import BillingClient

_CLOUD_BILLING_READONLY_SCOPE = "https://www.googleapis.com/auth/cloud-billing.readonly"
_ADC_SETUP_HINT = (
    "Enable the Cloud Billing API on your GCP project and run "
    "`gcloud auth application-default login` for local development."
)


_MAX_RETRIES = 6
_RETRY_BASE_SECONDS = 15.0


class GcpBillingClient(BillingClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._base_url = (base_url or settings.gcp_billing_base_url).rstrip("/")
        self._timeout = timeout_seconds
        self._credentials: Any | None = None

    def list_services(self) -> list[dict[str, Any]]:
        return self._paginate("/services")

    def list_skus_for_service(self, service_id: str) -> list[dict[str, Any]]:
        parent = f"services/{service_id}"
        return self._paginate(f"/{parent}/skus", extra_params={"currencyCode": "USD"})

    def _paginate(
        self,
        path: str,
        *,
        extra_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        resource_key = self._resource_key(path)

        while True:
            params: dict[str, str] = dict(extra_params or {})
            params["pageSize"] = "5000"
            if page_token:
                params["pageToken"] = page_token

            payload = self._get(path, params)
            items.extend(payload.get(resource_key, []))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        return items

    @staticmethod
    def _resource_key(path: str) -> str:
        if path.endswith("/skus"):
            return "skus"
        return "services"

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = httpx.get(
                    url,
                    params=params,
                    headers=self._auth_headers(),
                    timeout=self._timeout,
                )
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
                    f"GCP Billing API request failed ({exc.response.status_code}): {exc.response.text}"
                )
                break
            except httpx.HTTPError as exc:
                last_error = ServiceUnavailableError(f"GCP Billing API request failed: {exc}")
                break
            else:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ServiceUnavailableError("GCP Billing API returned an unexpected response.")
                return payload

        if last_error is not None:
            raise last_error
        raise ServiceUnavailableError("GCP Billing API rate limit exceeded after retries.")

    def _auth_headers(self) -> dict[str, str]:
        token = self._get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def _get_access_token(self) -> str:
        try:
            import google.auth
            import google.auth.transport.requests
        except ImportError as exc:
            raise ServiceUnavailableError(
                "google-auth is required for GCP Billing API access."
            ) from exc

        if self._credentials is None or not self._credentials.valid:
            try:
                credentials, _ = google.auth.default(scopes=[_CLOUD_BILLING_READONLY_SCOPE])
            except Exception as exc:
                raise ServiceUnavailableError(
                    f"Application Default Credentials unavailable. {_ADC_SETUP_HINT}"
                ) from exc

            request = google.auth.transport.requests.Request()
            try:
                credentials.refresh(request)
            except Exception as exc:
                raise ServiceUnavailableError(
                    f"Failed to refresh GCP credentials. {_ADC_SETUP_HINT}"
                ) from exc

            self._credentials = credentials

        token = getattr(self._credentials, "token", None)
        if not token:
            raise ServiceUnavailableError(
                f"GCP credentials did not return an access token. {_ADC_SETUP_HINT}"
            )
        return str(token)
