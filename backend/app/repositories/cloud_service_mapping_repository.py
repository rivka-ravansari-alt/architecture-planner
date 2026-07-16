"""Cloud service mapping persistence (Firestore ``cloud_service_mappings`` collection)."""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from app.config.params import FIRESTORE_CLOUD_SERVICE_MAPPINGS_COLLECTION


class CloudServiceMappingRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._collection = client.collection(
            FIRESTORE_CLOUD_SERVICE_MAPPINGS_COLLECTION
        )

    def upsert(
        self, category_id: str, providers: dict[str, list[dict[str, Any]]]
    ) -> bool:
        """Create or update a mapping by category id and return True when newly created.

        The document id is the ``category_id`` so re-running never produces
        duplicates and never removes mappings absent from the input.
        """

        reference = self._collection.document(category_id)
        existed = reference.get().exists
        reference.set(
            {
                "category_id": category_id,
                "providers": providers,
            }
        )
        return not existed

    def find_by_id(self, category_id: str) -> dict[str, Any] | None:
        """Return a single mapping document (with its id) or ``None``."""

        snapshot = self._collection.document(category_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["category_id"] = snapshot.id
        return data
