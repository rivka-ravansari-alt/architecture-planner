"""Project persistence (Firestore ``projects`` collection)."""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from app.config.params import (
    FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
)
from app.schemas.project import CreateProjectRequest


class ProjectRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._collection = client.collection(FIRESTORE_PROJECTS_COLLECTION)

    def create(self, payload: CreateProjectRequest, user_id: str) -> str:
        """Persist a new project and return the generated Firestore document id."""

        document = {
            "description": payload.description,
            "stage": payload.stage,
            "expected_users": payload.expected_users,
            "requirements": payload.requirements,
            "current_step": 1,
            "user_id": user_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        _, reference = self._collection.add(document)
        return reference.id

    def find_by_id(self, project_id: str) -> dict[str, Any] | None:
        """Return the project document (with its id) or ``None`` when missing."""

        snapshot = self._collection.document(project_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    def save_architecture_selection(
        self, project_id: str, selection: dict[str, Any]
    ) -> str:
        """Persist a component selection under the project and return its id.

        Written to ``projects/{project_id}/architecture_selections/{selection_id}``.
        The caller supplies an already-validated, server-timestamped document.
        """

        reference = (
            self._collection.document(project_id)
            .collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
            .document()
        )
        reference.set(selection)
        self._collection.document(project_id).set(
            {"current_step": 2, "updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )
        return reference.id

    def get_latest_architecture_selection(
        self, project_id: str
    ) -> dict[str, Any] | None:
        """Return the most recent architecture selection (with its id) or ``None``.

        Selections are append-only history documents; the latest one (by
        ``created_at``) is the live selection the user is reviewing.
        """

        query = (
            self._collection.document(project_id)
            .collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        for snapshot in query.stream():
            data = snapshot.to_dict() or {}
            data["id"] = snapshot.id
            return data
        return None

    def get_architecture_selection(
        self, project_id: str, selection_id: str
    ) -> dict[str, Any] | None:
        """Return a specific architecture selection document (with its id)."""

        snapshot = (
            self._collection.document(project_id)
            .collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
            .document(selection_id)
            .get()
        )
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    def update_architecture_selection(
        self,
        project_id: str,
        selection_id: str,
        selected: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
    ) -> None:
        """Overwrite the selected/excluded lists of an existing selection document.

        Only the manually editable lists are touched; the original run metadata
        (``model_output``, ``input``, etc.) is preserved via a merge write.
        """

        reference = (
            self._collection.document(project_id)
            .collection(FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION)
            .document(selection_id)
        )
        reference.set(
            {
                "selected": selected,
                "excluded": excluded,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        self._collection.document(project_id).set(
            {"updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )
