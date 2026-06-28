"""Firestore repository for price_import_runs."""

from __future__ import annotations

from typing import Any

from app.config.params import FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS
from app.pricing_ingestion.models.documents import PriceImportRunRecord


class PriceImportRunsRepository:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._collection = FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS

    def create(self, record: PriceImportRunRecord) -> None:
        self._client.collection(self._collection).document(record.id).set(record.to_dict())

    def update(self, record: PriceImportRunRecord) -> None:
        self._client.collection(self._collection).document(record.id).set(
            record.to_dict(),
            merge=True,
        )

    def get(self, run_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection(self._collection).document(run_id).get()
        if not getattr(snapshot, "exists", False):
            return None
        return snapshot.to_dict()
