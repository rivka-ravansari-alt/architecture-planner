"""Shared Firestore catalog repository logic."""

from __future__ import annotations

from typing import Any

from app.utils.slug import slugify


class BaseCatalogRepository:
    """Common CRUD and listing helpers for provider catalog collections."""

    def __init__(self, client: Any, *, collection: str) -> None:
        self._client = client
        self._collection = collection

    def upsert(self, record: Any) -> str:
        doc_ref = self._client.collection(self._collection).document(record.id)
        payload = {**record.to_dict(), "enabled": True}
        doc_ref.set(payload, merge=True)
        return record.id

    def delete(self, catalog_id: str) -> None:
        self._client.collection(self._collection).document(catalog_id).delete()

    def register_service_name(self, service_name: str) -> str:
        catalog_id = slugify(service_name)
        doc_ref = self._client.collection(self._collection).document(catalog_id)
        doc_ref.set({"id": catalog_id, "name": service_name, "enabled": True}, merge=True)
        return catalog_id

    def list_enabled_service_names(self) -> list[str]:
        seen: set[str] = set()
        names: list[str] = []

        for snapshot in self._client.collection(self._collection).stream():
            data = snapshot.to_dict() or {}
            if data.get("enabled") is not True:
                continue

            service_name = str(data.get("name", "")).strip()
            if not service_name:
                continue

            key = service_name.casefold()
            if key in seen:
                continue
            seen.add(key)
            names.append(service_name)

        return sorted(names, key=str.casefold)

    def get(self, catalog_id: str) -> dict[str, Any] | None:
        snapshot = self._client.collection(self._collection).document(catalog_id).get()
        if not getattr(snapshot, "exists", False):
            return None
        return snapshot.to_dict()
