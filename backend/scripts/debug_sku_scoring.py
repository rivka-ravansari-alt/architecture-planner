"""Debug SKU scoring for problematic services."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.services.pricing.catalog_lookup import PricingCatalogLookup
from app.services.pricing.component_models import (
    _haystack,
    _pick_best,
    _score_api_gateway_requests,
    _score_queue_requests,
    _score_nosql_requests,
)


def _top_scores(skus: dict, scorer, limit=8):
    scored = []
    for role, sku in skus.items():
        price = float(sku.get("unit_price_usd", 0) or 0)
        if price <= 0:
            continue
        score = scorer(role, sku)
        scored.append((score, role, price, sku.get("description", "")[:80], sku.get("usage_unit", "")))
    scored.sort()
    return scored[:limit]


def main() -> None:
    lookup = PricingCatalogLookup.from_firestore_client(FirestoreClientFactory.create())
    targets = [
        ("gcp", "API Gateway", _score_api_gateway_requests),
        ("gcp", "Cloud Pub/Sub", _score_queue_requests),
        ("gcp", "Cloud Firestore", _score_nosql_requests),
        ("azure", "API Management", _score_api_gateway_requests),
        ("azure", "Foundry Models", None),
    ]
    from app.services.pricing.component_models import _score_ai_inference

    for provider, service, scorer in targets:
        if scorer is None:
            scorer = _score_ai_inference
        catalog = lookup.lookup(provider, service)
        if not catalog:
            print(f"MISSING {provider}/{service}")
            continue
        skus = catalog.get("skus", {})
        print(f"\n=== {provider} / {service} ({len(skus)} skus) ===")
        picked = _pick_best(skus, scorer, [], label="debug")
        if picked:
            print(
                "PICKED:",
                picked.get("_source_role"),
                picked.get("unit_price_usd"),
                picked.get("usage_unit"),
                str(picked.get("description", ""))[:100],
            )
        else:
            print("PICKED: none")
        for score, role, price, desc, unit in _top_scores(skus, scorer):
            print(f"  {score:5.0f} {role:40} ${price:12.6f} {unit:8} {desc}")


if __name__ == "__main__":
    main()
