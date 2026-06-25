"""Component catalog persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.params import COMPONENT_CATEGORY_SUPPORTING
from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
from app.models.component_catalog import ComponentCatalog
from app.repositories.base import BaseRepository


class ComponentCatalogRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_active(self) -> list[ComponentCatalog]:
        stmt = (
            select(ComponentCatalog)
            .where(ComponentCatalog.is_active.is_(True))
            .order_by(ComponentCatalog.name)
        )
        return list(self._db.scalars(stmt).all())

    def find_by_name(self, name: str) -> ComponentCatalog | None:
        normalized = name.strip().lower()
        stmt = select(ComponentCatalog).where(ComponentCatalog.name == normalized)
        return self._db.scalars(stmt).first()

    def active_type_names(self) -> frozenset[str]:
        return frozenset(entry.name for entry in self.list_active())

    def types_by_category(self, category: str) -> frozenset[str]:
        return frozenset(
            entry.name for entry in self.list_active() if entry.category == category
        )

    def supporting_infrastructure_types(self) -> frozenset[str]:
        return self.types_by_category(COMPONENT_CATEGORY_SUPPORTING)

    def seed_if_empty(self) -> None:
        existing = self._db.scalar(select(ComponentCatalog.id).limit(1))
        if existing is not None:
            return
        for item in COMPONENT_CATALOG_SEED:
            self._db.add(
                ComponentCatalog(
                    name=str(item["name"]),
                    category=str(item["category"]),
                    description=str(item["description"]),
                    aws_options=list(item["aws_options"]),
                    gcp_options=list(item["gcp_options"]),
                    azure_options=list(item["azure_options"]),
                    is_active=True,
                )
            )
        self._db.commit()

    def backfill_categories(self) -> None:
        category_by_name = {
            str(item["name"]): str(item["category"]) for item in COMPONENT_CATALOG_SEED
        }
        updated = False
        for entry in self._db.scalars(select(ComponentCatalog)).all():
            expected = category_by_name.get(entry.name)
            if expected and entry.category != expected:
                entry.category = expected
                updated = True
        if updated:
            self._db.commit()
