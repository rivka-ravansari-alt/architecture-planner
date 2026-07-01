"""Read ArchSari pricing profile documents from Firestore."""

from __future__ import annotations

from typing import Any

from app.config.params import PRICING_PROFILE_COLLECTION_BY_PROVIDER
from app.services.cost_calculation.models import BillableSkuConfig, PricingProfile
from app.utils.slug import slugify


class PricingProfileRepository:
    """Access pricing calculation profiles independent of catalog price sync."""

    def __init__(self, firestore_client: Any) -> None:
        self._client = firestore_client

    def get_by_service_name(self, provider: str, service_name: str) -> PricingProfile | None:
        normalized_name = service_name.strip()
        if not normalized_name:
            return None

        collection = self._collection_for(provider)
        doc_id = profile_doc_id(normalized_name)
        by_id = self._profile_from_doc(self._get_doc(collection, doc_id), provider=provider)
        if by_id is not None:
            return by_id

        return self._find_by_name(collection, provider, normalized_name)

    def _collection_for(self, provider: str) -> str:
        try:
            return PRICING_PROFILE_COLLECTION_BY_PROVIDER[provider]
        except KeyError as exc:
            raise ValueError(f"Unsupported pricing provider '{provider}'") from exc

    def _get_doc(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection(collection).document(doc_id).get()
        if not getattr(snapshot, "exists", False):
            return None
        return snapshot.to_dict()

    def _find_by_name(self, collection: str, provider: str, service_name: str) -> PricingProfile | None:
        target_name = service_name.casefold()
        for snapshot in self._client.collection(collection).stream():
            data = snapshot.to_dict() or {}
            if data.get("enabled") is False:
                continue
            doc_name = str(data.get("service_name", "")).strip()
            if doc_name.casefold() != target_name:
                continue
            return self._profile_from_doc(data, provider=provider)
        return None

    @staticmethod
    def _profile_from_doc(doc: dict[str, Any] | None, *, provider: str) -> PricingProfile | None:
        if not doc:
            return None

        doc_provider = str(doc.get("provider", provider)).strip() or provider
        service_name = str(doc.get("service_name", "")).strip()
        pricing_model = str(doc.get("pricing_model", "")).strip()
        if not service_name or not pricing_model:
            return None

        raw_billable = doc.get("billable_skus")
        if not isinstance(raw_billable, dict) or not raw_billable:
            return None

        billable_skus: dict[str, BillableSkuConfig] = {}
        for role, config in raw_billable.items():
            if not isinstance(config, dict):
                continue
            usage_metric = str(config.get("usage_metric", "")).strip()
            conversion = str(config.get("conversion", "none")).strip() or "none"
            if not usage_metric:
                continue
            billable_skus[str(role).strip()] = BillableSkuConfig(
                usage_metric=usage_metric,
                conversion=conversion,
            )

        if not billable_skus:
            return None

        ignored_raw = doc.get("ignored_sku_roles", [])
        ignored_roles = (
            [str(role).strip() for role in ignored_raw if str(role).strip()]
            if isinstance(ignored_raw, list)
            else []
        )

        doc_id = str(doc.get("id", "")).strip() or profile_doc_id(service_name)
        enabled = doc.get("enabled", True) is not False

        return PricingProfile(
            id=doc_id,
            provider=doc_provider,
            service_name=service_name,
            pricing_model=pricing_model,
            billable_skus=billable_skus,
            ignored_sku_roles=ignored_roles,
            enabled=enabled,
        )


def profile_doc_id(service_name: str) -> str:
    return slugify(service_name)
