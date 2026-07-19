"""Project persistence (Firestore ``projects`` collection)."""

from __future__ import annotations

from typing import Any

from google.cloud import firestore

from app.config.params import (
    FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION,
    FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION,
    FIRESTORE_PRICING_RUNS_SUBCOLLECTION,
    FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
    PRICING_GENERATION_ORDER,
)
from app.schemas.project import CreateProjectRequest


class ProjectRepository:
    def __init__(self, client: firestore.Client) -> None:
        self._client = client
        self._collection = client.collection(FIRESTORE_PROJECTS_COLLECTION)

    def create(self, payload: CreateProjectRequest, user_id: str) -> str:
        """Persist a new project and return the generated Firestore document id."""

        document = {
            "description": payload.description,
            "platform": payload.platform,
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
        self.invalidate_downstream_artifacts(project_id)

    def mark_global_usage_model_stale(self, project_id: str, model_id: str) -> None:
        """Mark a global usage model as stale after the component selection changes."""

        (
            self._collection.document(project_id)
            .collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .document(model_id)
            .set({"stale": True, "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
        )

    def mark_pricing_run_stale(self, project_id: str, run_id: str) -> None:
        """Mark a pricing run as stale after the component selection changes."""

        (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .document(run_id)
            .set({"stale": True, "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)
        )

    def invalidate_downstream_artifacts(self, project_id: str) -> None:
        """Mark the latest usage model and pricing run stale for this project."""

        usage_model = self.get_latest_global_usage_model(project_id)
        if usage_model is not None and not usage_model.get("stale"):
            self.mark_global_usage_model_stale(project_id, usage_model["id"])

        pricing_run = self.get_latest_pricing_run(project_id)
        if pricing_run is not None and not pricing_run.get("stale"):
            self.mark_pricing_run_stale(project_id, pricing_run["id"])

    def save_global_usage_model(
        self, project_id: str, usage_model: dict[str, Any]
    ) -> str:
        """Persist a global usage model under the project and return its id.

        Written to ``projects/{project_id}/global_usage_models/{model_id}``.

        Each document stores the exact LLM prompt, raw OpenAI response (unchanged
        after validation), validated ``model_output``, combined ``usage_model``,
        model name, ``selection_id``, and ``created_at``.
        """

        reference = (
            self._collection.document(project_id)
            .collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .document()
        )
        reference.set(usage_model)
        self._collection.document(project_id).set(
            {"current_step": 3, "updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )
        return reference.id

    def get_global_usage_model(
        self, project_id: str, model_id: str
    ) -> dict[str, Any] | None:
        """Return a specific global usage model (with its id) or ``None``."""

        snapshot = (
            self._collection.document(project_id)
            .collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .document(model_id)
            .get()
        )
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    def create_global_usage_model_if_absent(
        self, project_id: str, model_id: str, usage_model: dict[str, Any]
    ) -> tuple[str, bool]:
        """Atomically create the usage-model document only if it isn't already present.

        Uses a Firestore transaction keyed on the deterministic ``model_id`` so that
        concurrent Step-3 requests with identical inputs converge on a single
        document: exactly one caller creates it, and the rest reuse it. Returns the
        model id and whether this call created the document (``False`` == reused).
        """

        reference = (
            self._collection.document(project_id)
            .collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .document(model_id)
        )
        transaction = self._client.transaction()
        created = _create_global_usage_model_if_absent(
            transaction, reference, usage_model
        )
        if created:
            self._collection.document(project_id).set(
                {"current_step": 3, "updated_at": firestore.SERVER_TIMESTAMP},
                merge=True,
            )
        return model_id, created

    def update_global_usage_model_debug_csv_path(
        self, project_id: str, model_id: str, object_path: str
    ) -> None:
        """Store Step 3 usage-model debug CSV object path.

        Written to ``projects/{project_id}/global_usage_models/{model_id}``.
        """

        (
            self._collection.document(project_id)
            .collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .document(model_id)
            .set(
                {
                    "usage_model_debug_csv_object_path": object_path,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )
        )

    def get_latest_global_usage_model(
        self, project_id: str
    ) -> dict[str, Any] | None:
        """Return the most recent global usage model (with its id) or ``None``."""

        query = (
            self._collection.document(project_id)
            .collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        for snapshot in query.stream():
            data = snapshot.to_dict() or {}
            data["id"] = snapshot.id
            return data
        return None

    def set_current_step(self, project_id: str, step: int) -> None:
        """Update the project's current wizard step."""

        self._collection.document(project_id).set(
            {"current_step": step, "updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )

    def create_pricing_run(self, project_id: str, run: dict[str, Any]) -> str:
        """Persist a new pricing run and return its id."""

        reference = (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .document()
        )
        reference.set(run)
        return reference.id

    def get_pricing_run(self, project_id: str, run_id: str) -> dict[str, Any] | None:
        """Return a specific pricing run document (with its id) or ``None``."""

        snapshot = (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .document(run_id)
            .get()
        )
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        return data

    def get_latest_pricing_run(self, project_id: str) -> dict[str, Any] | None:
        """Return the most recent pricing run (with its id) or ``None``."""

        query = (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        for snapshot in query.stream():
            data = snapshot.to_dict() or {}
            data["id"] = snapshot.id
            return data
        return None

    def update_pricing_run(
        self, project_id: str, run_id: str, fields: dict[str, Any]
    ) -> None:
        """Merge-update fields on an existing pricing run."""

        (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .document(run_id)
            .set(fields, merge=True)
        )

    def save_provider_pricing_result(
        self,
        project_id: str,
        run_id: str,
        provider: str,
        result: dict[str, Any],
    ) -> None:
        """Persist one provider's pricing result under a pricing run."""

        (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .document(run_id)
            .collection(FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION)
            .document(provider)
            .set(result)
        )
        self._collection.document(project_id).set(
            {"updated_at": firestore.SERVER_TIMESTAMP},
            merge=True,
        )

    def list_provider_pricing_results(
        self, project_id: str, run_id: str
    ) -> list[dict[str, Any]]:
        """Return all provider pricing results for a run, ordered by generation."""

        snapshots = (
            self._collection.document(project_id)
            .collection(FIRESTORE_PRICING_RUNS_SUBCOLLECTION)
            .document(run_id)
            .collection(FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION)
            .stream()
        )
        results_by_provider = {
            snapshot.id: {**(snapshot.to_dict() or {}), "provider": snapshot.id}
            for snapshot in snapshots
        }
        return [
            results_by_provider[provider]
            for provider in PRICING_GENERATION_ORDER
            if provider in results_by_provider
        ]


@firestore.transactional
def _create_global_usage_model_if_absent(
    transaction: firestore.Transaction,
    reference: firestore.DocumentReference,
    usage_model: dict[str, Any],
) -> bool:
    """Create ``usage_model`` at ``reference`` only if no current document exists.

    Returns ``True`` when it wrote a new document, ``False`` when a non-stale
    document was already present (so the caller should reuse it).
    """

    snapshot = reference.get(transaction=transaction)
    if snapshot.exists and not (snapshot.to_dict() or {}).get("stale"):
        return False
    transaction.set(reference, usage_model)
    return True
