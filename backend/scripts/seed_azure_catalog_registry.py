"""Register Azure billing catalog service names in Firestore from the component catalog DB."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.repositories.component_catalog_repository import ComponentCatalogRepository


def main() -> None:
    with SessionLocal() as session:
        catalog_services = ComponentCatalogRepository(session).collect_azure_catalog_services()

    target_names = {service.name.casefold() for service in catalog_services}
    repo = AzureCatalogRepository(FirestoreClientFactory.create())
    client = FirestoreClientFactory.create()

    for snapshot in client.collection("azure_catalog").stream():
        data = snapshot.to_dict() or {}
        name = str(data.get("name", "")).strip()
        if name.casefold() not in target_names:
            repo.delete(snapshot.id)
            print(f"removed stale doc {snapshot.id!r} ({name!r})")

    for service in catalog_services:
        doc_id = repo.register_service_name(service.name)
        print(f"registered {service.name!r} -> {doc_id}")

    print(f"done: {len(catalog_services)} service names registered in azure_catalog")


if __name__ == "__main__":
    main()
