"""Architecture category persistence (Firestore ``architecture_categories`` collection)."""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from app.config.params import FIRESTORE_ARCHITECTURE_CATEGORIES_COLLECTION


class ArchitectureCategoryRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._collection = client.collection(
            FIRESTORE_ARCHITECTURE_CATEGORIES_COLLECTION
        )

    def upsert(self, category_id: str, name: str, description: str) -> bool:
        """Create or update a category by id and return True when newly created.

        Uses a merge write keyed on the category id so re-running never produces
        duplicates and never removes categories absent from the input.
        """

        reference = self._collection.document(category_id)
        existed = reference.get().exists
        reference.set(
            {
                "id": category_id,
                "name": name,
                "description": description,
            },
            merge=True,
        )
        return not existed

    def find_by_id(self, category_id: str) -> dict[str, Any] | None:
        """Return a single category document (with its id) or ``None``.

        The document id is authoritative for ``id``. Firestore remains the single
        source of truth for the category metadata (``name``/``description``/``type``).
        """

        snapshot = self._collection.document(category_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    def list_all(self) -> list[dict[str, Any]]:
        """Return every architecture category document.

        Firestore is the single source of truth for category data; the returned
        dicts carry whatever fields are stored (``id``, ``name``, ``description``
        and, when present, ``type``). The document id is authoritative for ``id``.
        """

        categories: list[dict[str, Any]] = []
        for snapshot in self._collection.stream():
            data = snapshot.to_dict() or {}
            data["id"] = snapshot.id
            categories.append(data)
        categories.sort(key=lambda category: category.get("name", category["id"]))
        return categories
