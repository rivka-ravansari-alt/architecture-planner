"""Firestore client factory."""

from __future__ import annotations

from typing import Any

from app.config.settings import settings

FIRESTORE_BATCH_LIMIT = 400


class FirestoreClientFactory:
    @staticmethod
    def create(client: Any | None = None) -> Any:
        if client is not None:
            return client

        from google.cloud import firestore

        project = settings.firestore_project_id or settings.gcs_project_id or None
        database = settings.firestore_database or None
        if project and database:
            return firestore.Client(project=project, database=database)
        if project:
            return firestore.Client(project=project)
        return firestore.Client()
