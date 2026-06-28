"""Firestore repository for gcp_catalog."""

from __future__ import annotations

from typing import Any

from app.config.params import FIRESTORE_COLLECTION_GCP_CATALOG
from app.pricing_ingestion.models.documents import GcpCatalogRecord
from app.pricing_ingestion.repositories.base_catalog_repository import BaseCatalogRepository


class GcpCatalogRepository(BaseCatalogRepository):
    def __init__(self, client: Any) -> None:
        super().__init__(client, collection=FIRESTORE_COLLECTION_GCP_CATALOG)

    def upsert(self, record: GcpCatalogRecord) -> str:
        return super().upsert(record)
