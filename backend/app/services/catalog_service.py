"""Catalog lookup helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.params import COMPONENT_CATEGORY_MAIN, LEGACY_COMPONENT_TYPES, PROJECT_TYPES
from app.repositories.component_catalog_repository import ComponentCatalogRepository
from app.schemas.project import ComponentCatalogOut, ProjectTypeInfo
from app.utils.component_type import normalize_component_type


class CatalogService:
    def __init__(
        self,
        db: Session,
        catalog_repo: ComponentCatalogRepository | None = None,
    ) -> None:
        self._catalog_repo = catalog_repo or ComponentCatalogRepository(db)

    def list_project_types(self) -> list[ProjectTypeInfo]:
        return [
            ProjectTypeInfo(
                id=item["type"],
                label=item["label"],
                description=item["description"],
            )
            for item in PROJECT_TYPES
        ]

    def list_component_catalog(self) -> list[ComponentCatalogOut]:
        return [
            ComponentCatalogOut.model_validate(entry)
            for entry in self._catalog_repo.list_active()
        ]

    def component_type_names(self) -> tuple[str, ...]:
        return tuple(entry.name for entry in self._catalog_repo.list_active())

    def prompt_component_type_list(self) -> str:
        return ", ".join(self.component_type_names())

    def valid_component_types(self) -> frozenset[str]:
        return self._catalog_repo.active_type_names() | LEGACY_COMPONENT_TYPES

    def normalize_component_type(self, component_type: str) -> str:
        return normalize_component_type(component_type)

    def supporting_infrastructure_types(self) -> frozenset[str]:
        return self._catalog_repo.supporting_infrastructure_types()

    def main_architecture_types(self) -> frozenset[str]:
        return self._catalog_repo.types_by_category(COMPONENT_CATEGORY_MAIN)
