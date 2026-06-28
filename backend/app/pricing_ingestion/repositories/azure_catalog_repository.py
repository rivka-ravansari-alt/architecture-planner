"""Firestore repository for azure_catalog."""

from __future__ import annotations

from typing import Any

from app.config.params import FIRESTORE_COLLECTION_AZURE_CATALOG
from app.pricing_ingestion.models.documents import AzureCatalogRecord
from app.pricing_ingestion.repositories.base_catalog_repository import BaseCatalogRepository


class AzureCatalogRepository(BaseCatalogRepository):
    def __init__(self, client: Any) -> None:
        super().__init__(client, collection=FIRESTORE_COLLECTION_AZURE_CATALOG)

    def upsert(self, record: AzureCatalogRecord) -> str:
        return super().upsert(record)
