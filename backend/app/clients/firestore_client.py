"""Firestore client provider.

Firestore is the only application database. The client authenticates via
Application Default Credentials (ADC); run `gcloud auth application-default
login` locally, or rely on the attached service account in the cloud.
"""

from __future__ import annotations

from functools import lru_cache

from google.cloud import firestore

from app.config.settings import settings


@lru_cache(maxsize=1)
def get_firestore_client() -> firestore.Client:
    """Return a process-wide cached Firestore client.

    The GCP project is taken from ``GCS_PROJECT_ID`` when set, otherwise
    it is inferred from the ambient ADC credentials.
    """

    project = settings.gcs_project_id or None
    return firestore.Client(project=project)
