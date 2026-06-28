"""Firestore document models for GCP catalog ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _iso(dt: datetime) -> str:
    return dt.isoformat()


@dataclass(frozen=True)
class ImportRunError:
    service_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"service_id": self.service_id, "message": self.message}


@dataclass
class PriceImportRunRecord:
    id: str
    provider: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    services_total: int = 0
    services_succeeded: int = 0
    services_failed: int = 0
    skus_upserted: int = 0
    errors: list[ImportRunError] = field(default_factory=list)
    triggered_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "started_at": _iso(self.started_at),
            "ended_at": _iso(self.ended_at) if self.ended_at else None,
            "services_total": self.services_total,
            "services_succeeded": self.services_succeeded,
            "services_failed": self.services_failed,
            "skus_upserted": self.skus_upserted,
            "errors": [error.to_dict() for error in self.errors],
            "triggered_by": self.triggered_by,
        }


@dataclass(frozen=True)
class GcpCatalogRecord:
    """One Firestore document per GCP product from architecture_components.gcp_options."""

    id: str
    name: str
    skus: dict[str, dict[str, Any]]
    formula: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "skus": self.skus,
            "formula": dict(self.formula),
        }

    @property
    def sku_count(self) -> int:
        return len(self.skus)


@dataclass(frozen=True)
class AzureCatalogRecord:
    """One Firestore document per Azure product from architecture_components.azure_options."""

    id: str
    name: str
    skus: dict[str, dict[str, Any]]
    formula: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "skus": self.skus,
            "formula": dict(self.formula),
        }

    @property
    def sku_count(self) -> int:
        return len(self.skus)


@dataclass(frozen=True)
class AwsCatalogRecord:
    """One Firestore document per AWS product from architecture_components.aws_options."""

    id: str
    name: str
    skus: dict[str, dict[str, Any]]
    formula: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "skus": self.skus,
            "formula": dict(self.formula),
        }

    @property
    def sku_count(self) -> int:
        return len(self.skus)
