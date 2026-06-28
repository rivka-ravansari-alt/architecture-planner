"""Load enabled Azure services from the component catalog database."""

from __future__ import annotations

from app.pricing_ingestion.models.azure_catalog_ref import AzureCatalogServiceRef
from app.repositories.component_catalog_repository import ComponentCatalogRepository


class DbAzureCatalogLoader:
    def __init__(self, catalog_repo: ComponentCatalogRepository) -> None:
        self._catalog_repo = catalog_repo

    def list_enabled_services(self) -> list[AzureCatalogServiceRef]:
        return self._catalog_repo.collect_azure_catalog_services()
