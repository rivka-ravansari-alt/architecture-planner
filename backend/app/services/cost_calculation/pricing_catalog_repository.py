"""Read normalized pricing records from Firestore provider catalogs."""

from __future__ import annotations

from typing import Any

from app.config.params import (
    FIRESTORE_COLLECTION_AWS_CATALOG,
    FIRESTORE_COLLECTION_AZURE_CATALOG,
    FIRESTORE_COLLECTION_GCP_CATALOG,
    PRICING_PROVIDER_AWS,
    PRICING_PROVIDER_AZURE,
    PRICING_PROVIDER_GCP,
)
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.services.cost_calculation.models import PricingCatalogRecord
from app.utils.slug import slugify


class PricingCatalogRepository:
    """Unified access to normalized pricing documents in Firestore."""

    _COLLECTION_BY_PROVIDER = {
        PRICING_PROVIDER_GCP: FIRESTORE_COLLECTION_GCP_CATALOG,
        PRICING_PROVIDER_AWS: FIRESTORE_COLLECTION_AWS_CATALOG,
        PRICING_PROVIDER_AZURE: FIRESTORE_COLLECTION_AZURE_CATALOG,
    }

    def __init__(self, firestore_client: Any) -> None:
        self._client = firestore_client
        self._repos = {
            PRICING_PROVIDER_GCP: GcpCatalogRepository(firestore_client),
            PRICING_PROVIDER_AWS: AwsCatalogRepository(firestore_client),
            PRICING_PROVIDER_AZURE: AzureCatalogRepository(firestore_client),
        }

    def get_by_service_name(self, provider: str, service_name: str) -> PricingCatalogRecord | None:
        normalized_name = service_name.strip()
        if not normalized_name:
            return None

        by_id = self._record_from_doc(provider, self._repos[provider].get(slugify(normalized_name)))
        if by_id is not None:
            return by_id

        return self._find_by_name(provider, normalized_name)

    def _find_by_name(self, provider: str, service_name: str) -> PricingCatalogRecord | None:
        target = service_name.casefold()
        collection = self._COLLECTION_BY_PROVIDER[provider]
        for snapshot in self._client.collection(collection).stream():
            data = snapshot.to_dict() or {}
            if data.get("enabled") is False:
                continue
            doc_name = str(data.get("name", "")).strip()
            if doc_name.casefold() != target:
                continue
            return self._record_from_doc(provider, data)
        return None

    @staticmethod
    def _record_from_doc(provider: str, doc: dict[str, Any] | None) -> PricingCatalogRecord | None:
        if not doc:
            return None

        skus = doc.get("skus")
        formula = doc.get("formula")
        if not isinstance(skus, dict) or not skus:
            return None
        if not formula:
            return None

        if isinstance(formula, str):
            normalized_formula: dict[str, str] | str = formula.strip()
        elif isinstance(formula, dict):
            normalized_formula = {str(k): str(v) for k, v in formula.items()}
        else:
            return None

        doc_id = str(doc.get("id", "")).strip() or slugify(str(doc.get("name", "")))
        name = str(doc.get("name", "")).strip() or doc_id
        return PricingCatalogRecord(
            id=doc_id,
            name=name,
            provider=provider,
            skus=skus,
            formula=normalized_formula,
        )
