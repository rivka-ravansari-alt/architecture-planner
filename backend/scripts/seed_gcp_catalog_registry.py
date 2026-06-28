"""Register enabled GCP billing catalog service names in Firestore."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.params import GCP_CATALOG_SKIP_OPTIONS
from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository


def collect_service_names_from_catalog_seed() -> list[str]:
    seen: set[str] = set()
    names: list[str] = []

    for entry in COMPONENT_CATALOG_SEED:
        for raw_option in entry["gcp_options"]:
            option = str(raw_option).strip()
            if not option or option in GCP_CATALOG_SKIP_OPTIONS:
                continue
            key = option.casefold()
            if key in seen:
                continue
            seen.add(key)
            names.append(option)

    return sorted(names, key=str.casefold)


def main() -> None:
    service_names = collect_service_names_from_catalog_seed()
    target_names = {name.casefold() for name in service_names}
    repo = GcpCatalogRepository(FirestoreClientFactory.create())
    client = FirestoreClientFactory.create()

    for snapshot in client.collection("gcp_catalog").stream():
        data = snapshot.to_dict() or {}
        name = str(data.get("name", "")).strip()
        if name.casefold() not in target_names:
            repo.delete(snapshot.id)
            print(f"removed stale doc {snapshot.id!r} ({name!r})")

    for service_name in service_names:
        doc_id = repo.register_service_name(service_name)
        print(f"registered {service_name!r} -> {doc_id}")

    print(f"done: {len(service_names)} service names registered in gcp_catalog")


if __name__ == "__main__":
    main()
