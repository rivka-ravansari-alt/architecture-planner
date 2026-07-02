"""Seed Firestore pricing_component_profiles from the current Python defaults.

This script moves component pricing rules into Firestore while leaving SKU prices
in the existing provider catalog collections.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.services.pricing.component_profiles import iter_default_profile_documents
from app.services.pricing.pricing_profile_repository import PricingProfileRepository


def main() -> None:
    client = FirestoreClientFactory.create()
    repository = PricingProfileRepository(client)
    docs = iter_default_profile_documents()

    written: list[str] = []
    for doc in docs:
        written.append(repository.upsert(doc))

    print(
        json.dumps(
            {
                "collection": "pricing_component_profiles",
                "profiles_written": len(written),
                "document_ids": written,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
