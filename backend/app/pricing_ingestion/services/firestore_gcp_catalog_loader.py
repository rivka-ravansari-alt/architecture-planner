"""Load enabled GCP service names from Firestore gcp_catalog."""

from __future__ import annotations

from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository


class FirestoreGcpCatalogLoader:
    def __init__(self, catalog_repo: GcpCatalogRepository) -> None:
        self._catalog_repo = catalog_repo

    def list_enabled_service_names(self) -> list[str]:
        return self._catalog_repo.list_enabled_service_names()
