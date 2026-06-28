"""Load enabled AWS services from the component catalog database."""

from __future__ import annotations

from app.pricing_ingestion.models.aws_catalog_ref import AwsCatalogServiceRef
from app.repositories.component_catalog_repository import ComponentCatalogRepository


class DbAwsCatalogLoader:
    def __init__(self, catalog_repo: ComponentCatalogRepository) -> None:
        self._catalog_repo = catalog_repo

    def list_enabled_services(self) -> list[AwsCatalogServiceRef]:
        return self._catalog_repo.collect_aws_catalog_services()
