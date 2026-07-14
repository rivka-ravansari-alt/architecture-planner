"""User persistence (Firestore ``users`` collection)."""

from __future__ import annotations

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.config.params import FIRESTORE_USERS_COLLECTION
from app.schemas.auth import UserOut


def _doc_to_user(doc: firestore.DocumentSnapshot) -> UserOut:
    data = doc.to_dict() or {}
    return UserOut(
        id=doc.id,
        email=data.get("email", ""),
        name=data.get("name", ""),
        picture=data.get("picture"),
    )


class UserRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._collection = client.collection(FIRESTORE_USERS_COLLECTION)

    def find_by_id(self, user_id: str) -> UserOut | None:
        snapshot = self._collection.document(user_id).get()
        if not snapshot.exists:
            return None
        return _doc_to_user(snapshot)

    def find_by_google_sub(self, google_sub: str) -> firestore.DocumentSnapshot | None:
        results = list(
            self._collection.where(
                filter=FieldFilter("google_sub", "==", google_sub)
            )
            .limit(1)
            .stream()
        )
        return results[0] if results else None

    def upsert_by_google_sub(
        self,
        *,
        google_sub: str,
        email: str,
        name: str,
        picture: str | None,
    ) -> UserOut:
        existing = self.find_by_google_sub(google_sub)
        if existing is not None:
            reference = existing.reference
            reference.update(
                {
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "last_login_at": firestore.SERVER_TIMESTAMP,
                }
            )
            return _doc_to_user(reference.get())

        document = {
            "google_sub": google_sub,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_login_at": firestore.SERVER_TIMESTAMP,
        }
        _, reference = self._collection.add(document)
        return _doc_to_user(reference.get())
