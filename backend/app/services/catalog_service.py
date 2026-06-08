"""Catalog lookup helpers."""

from __future__ import annotations

from app.config.params import PROJECT_TYPES
from app.schemas.project import ProjectTypeInfo


class CatalogService:
    def list_project_types(self) -> list[ProjectTypeInfo]:
        return [
            ProjectTypeInfo(
                id=item["type"],
                label=item["label"],
                description=item["description"],
            )
            for item in PROJECT_TYPES
        ]
