"""In-memory Firestore substitute for unit tests."""

from __future__ import annotations

from typing import Any


class FakeDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any] | None, *, exists: bool) -> None:
        self.id = doc_id
        self._data = data
        self.exists = exists

    def to_dict(self) -> dict[str, Any] | None:
        return self._data


class FakeDocumentReference:
    def __init__(self, store: dict[str, dict[str, Any]], collection: str, doc_id: str) -> None:
        self._store = store
        self._collection = collection
        self._doc_id = doc_id

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        bucket = self._store.setdefault(self._collection, {})
        if merge and self._doc_id in bucket:
            bucket[self._doc_id] = {**bucket[self._doc_id], **data}
        else:
            bucket[self._doc_id] = dict(data)

    def delete(self) -> None:
        bucket = self._store.get(self._collection, {})
        bucket.pop(self._doc_id, None)

    def get(self) -> FakeDocumentSnapshot:
        bucket = self._store.get(self._collection, {})
        if self._doc_id not in bucket:
            return FakeDocumentSnapshot(self._doc_id, None, exists=False)
        return FakeDocumentSnapshot(self._doc_id, dict(bucket[self._doc_id]), exists=True)


class FakeCollectionReference:
    def __init__(self, store: dict[str, dict[str, Any]], collection: str) -> None:
        self._store = store
        self._collection = collection

    def document(self, doc_id: str) -> FakeDocumentReference:
        return FakeDocumentReference(self._store, self._collection, doc_id)

    def stream(self):
        bucket = self._store.get(self._collection, {})
        for doc_id, data in bucket.items():
            yield FakeDocumentSnapshot(doc_id, dict(data), exists=True)


class FakeWriteBatch:
    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store
        self._ops: list[tuple[str, str, dict[str, Any], bool]] = []

    def set(self, doc_ref: FakeDocumentReference, data: dict[str, Any], merge: bool = False) -> None:
        self._ops.append((doc_ref._collection, doc_ref._doc_id, data, merge))

    def commit(self) -> None:
        for collection, doc_id, data, merge in self._ops:
            ref = FakeDocumentReference(self._store, collection, doc_id)
            ref.set(data, merge=merge)
        self._ops.clear()


class FakeFirestoreClient:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def collection(self, name: str) -> FakeCollectionReference:
        return FakeCollectionReference(self._store, name)

    def batch(self) -> FakeWriteBatch:
        return FakeWriteBatch(self._store)

    def dump(self) -> dict[str, dict[str, Any]]:
        return self._store

    def seed_gcp_catalog_names(self, names: list[str]) -> None:
        from app.utils.slug import slugify

        for name in names:
            doc_id = slugify(name)
            self._store.setdefault("gcp_catalog", {})[doc_id] = {
                "id": doc_id,
                "name": name,
                "enabled": True,
            }

    def seed_azure_catalog_names(self, names: list[str]) -> None:
        from app.utils.slug import slugify

        for name in names:
            doc_id = slugify(name)
            self._store.setdefault("azure_catalog", {})[doc_id] = {
                "id": doc_id,
                "name": name,
                "enabled": True,
            }
