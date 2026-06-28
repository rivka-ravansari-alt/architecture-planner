"""Firestore repository for aws_catalog."""

from __future__ import annotations

from typing import Any

from app.config.params import FIRESTORE_COLLECTION_AWS_CATALOG
from app.pricing_ingestion.models.documents import AwsCatalogRecord
from app.pricing_ingestion.repositories.base_catalog_repository import BaseCatalogRepository


class AwsCatalogRepository(BaseCatalogRepository):
    def __init__(self, client: Any) -> None:
        super().__init__(client, collection=FIRESTORE_COLLECTION_AWS_CATALOG)

    def upsert(self, record: AwsCatalogRecord) -> str:
        return super().upsert(record)
