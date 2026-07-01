"""Backfill ArchSari pricing profiles into Firestore."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.params import (
    FIRESTORE_COLLECTION_PRICING_PROFILES,
    PRICING_PROFILE_COLLECTION_BY_PROVIDER,
    PRICING_PROVIDERS,
)
from app.data.pricing_profiles_seed import all_pricing_profile_docs, collect_catalog_service_names
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.services.cost_calculation.pricing_profile_repository import profile_doc_id


def main() -> None:
    client = FirestoreClientFactory.create()
    target_ids_by_provider = {
        provider: {profile_doc_id(name) for name in names}
        for provider, names in collect_catalog_service_names().items()
    }

    for provider in PRICING_PROVIDERS:
        collection = PRICING_PROFILE_COLLECTION_BY_PROVIDER[provider]
        target_ids = target_ids_by_provider[provider]
        for snapshot in client.collection(collection).stream():
            if snapshot.id not in target_ids:
                snapshot.reference.delete()
                print(f"removed stale profile {collection}/{snapshot.id!r}")

    for doc in all_pricing_profile_docs():
        collection = PRICING_PROFILE_COLLECTION_BY_PROVIDER[doc["provider"]]
        client.collection(collection).document(doc["id"]).set(doc, merge=True)
        print(f"upserted profile {collection}/{doc['service_name']} -> {doc['id']}")

    legacy_removed = 0
    for snapshot in client.collection(FIRESTORE_COLLECTION_PRICING_PROFILES).stream():
        snapshot.reference.delete()
        legacy_removed += 1
    if legacy_removed:
        print(f"removed {legacy_removed} legacy doc(s) from {FIRESTORE_COLLECTION_PRICING_PROFILES!r}")

    print(
        "done: "
        f"{len(all_pricing_profile_docs())} pricing profiles across "
        f"{', '.join(PRICING_PROFILE_COLLECTION_BY_PROVIDER.values())}"
    )


if __name__ == "__main__":
    main()
