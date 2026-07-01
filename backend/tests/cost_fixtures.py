"""Firestore pricing fixtures derived from the component catalog seed."""

from __future__ import annotations

from app.config.params import (
    CLOUD_OPTION_SKIP_VALUES,
    FIRESTORE_COLLECTION_AWS_CATALOG,
    FIRESTORE_COLLECTION_AZURE_CATALOG,
    FIRESTORE_COLLECTION_GCP_CATALOG,
    PRICING_PROFILE_COLLECTION_BY_PROVIDER,
)
from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
from app.data.pricing_profiles_seed import build_pricing_profile_doc
from app.pricing_ingestion.models.aws_catalog_ref import aws_option_display_name
from app.pricing_ingestion.models.azure_catalog_ref import azure_option_display_name
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.utils.slug import slugify

_COLLECTION_BY_PROVIDER = {
    "aws": FIRESTORE_COLLECTION_AWS_CATALOG,
    "gcp": FIRESTORE_COLLECTION_GCP_CATALOG,
    "azure": FIRESTORE_COLLECTION_AZURE_CATALOG,
}


def _is_billable_option(name: str) -> bool:
    return bool(name) and name.casefold() not in CLOUD_OPTION_SKIP_VALUES


def _catalog_service_names() -> dict[str, list[str]]:
    names_by_provider: dict[str, set[str]] = {provider: set() for provider in _COLLECTION_BY_PROVIDER}

    for entry in COMPONENT_CATALOG_SEED:
        for option in entry.get("aws_options", []):
            name = aws_option_display_name(option)
            if _is_billable_option(name):
                names_by_provider["aws"].add(name)
        for option in entry.get("gcp_options", []):
            name = str(option).strip()
            if _is_billable_option(name):
                names_by_provider["gcp"].add(name)
        for option in entry.get("azure_options", []):
            name = azure_option_display_name(option)
            if _is_billable_option(name):
                names_by_provider["azure"].add(name)

    return {
        _COLLECTION_BY_PROVIDER[provider]: sorted(names, key=str.casefold)
        for provider, names in names_by_provider.items()
    }


def _storage_formula() -> dict[str, str]:
    return {
        "storage_cost": "storage_gb * skus.storage.unit_price_usd",
        "total": "storage_cost",
    }


def _compute_formula() -> dict[str, str]:
    return {
        "cpu_cost": "monthly_requests * avg_request_duration * cpu * skus.cpu.unit_price_usd",
        "memory_cost": "monthly_requests * avg_request_duration * memory * skus.memory.unit_price_usd",
        "request_cost": "(monthly_requests / 1000000) * skus.requests.unit_price_usd",
        "total": "cpu_cost + memory_cost + request_cost",
    }


def _compute_skus(doc_id: str) -> dict[str, dict[str, object]]:
    return {
        "cpu": {"sku_id": f"{doc_id}-cpu", "unit_price_usd": 0.000024, "usage_unit": "vcpu-hour"},
        "memory": {"sku_id": f"{doc_id}-mem", "unit_price_usd": 0.0000025, "usage_unit": "gib-hour"},
        "requests": {"sku_id": f"{doc_id}-req", "unit_price_usd": 0.40, "usage_unit": "1M requests"},
    }


def _instance_doc(doc_id: str, name: str, hourly_price: float = 0.01) -> dict[str, object]:
    return {
        "id": doc_id,
        "name": name,
        "enabled": True,
        "skus": {
            "hour": {
                "sku_id": f"{doc_id}-hour",
                "unit_price_usd": hourly_price,
                "usage_unit": "hour",
            },
            "instance": {
                "sku_id": f"{doc_id}-instance",
                "unit_price_usd": 5.0,
                "usage_unit": "mo",
            },
        },
        "formula": "instance_based",
    }


def _pricing_doc_for_service(name: str) -> dict[str, object]:
    doc_id = slugify(name)
    lowered = name.casefold()

    if "storage" in lowered or lowered in {"s3", "blob storage"}:
        return {
            "id": doc_id,
            "name": name,
            "enabled": True,
            "skus": {
                "storage": {
                    "sku_id": f"{doc_id}-storage",
                    "unit_price_usd": 0.023,
                    "usage_unit": "GiBy.mo",
                }
            },
            "formula": _storage_formula(),
        }

    if any(
        token in lowered
        for token in (
            "api gateway",
            "api management",
            "cloud run",
            "lambda",
            "fargate",
            "functions",
            "cloud functions",
        )
    ):
        return {
            "id": doc_id,
            "name": name,
            "enabled": True,
            "skus": _compute_skus(doc_id),
            "formula": _compute_formula(),
        }

    if any(
        token in lowered
        for token in ("hosting", "amplify", "firebase", "app service", "static web")
    ):
        return _instance_doc(doc_id, name, hourly_price=0.005)

    if any(token in lowered for token in ("monitor", "cloudwatch", "log analytics", "logging")):
        return {
            "id": doc_id,
            "name": name,
            "enabled": True,
            "skus": {
                "log": {
                    "sku_id": f"{doc_id}-log",
                    "unit_price_usd": 0.50,
                    "usage_unit": "GiBy",
                    "description": "Log ingestion",
                },
                "metrics": {
                    "sku_id": f"{doc_id}-metrics",
                    "unit_price_usd": 0.10,
                    "usage_unit": "1K metrics",
                    "description": "Custom metrics",
                },
            },
            "formula": "monitoring_based",
        }

    if any(token in lowered for token in ("notification", "sns", "ses", "pub/sub")):
        return {
            "id": doc_id,
            "name": name,
            "enabled": True,
            "skus": {
                "email": {"sku_id": f"{doc_id}-email", "unit_price_usd": 0.10, "usage_unit": "1K emails"},
                "push": {"sku_id": f"{doc_id}-push", "unit_price_usd": 0.05, "usage_unit": "1K push"},
                "sms": {"sku_id": f"{doc_id}-sms", "unit_price_usd": 0.01, "usage_unit": "sms"},
            },
            "formula": "notification_based",
        }

    if any(token in lowered for token in ("firestore", "dynamodb", "cosmos", "database", "rds")):
        return {
            "id": doc_id,
            "name": name,
            "enabled": True,
            "skus": {
                "reads": {"sku_id": f"{doc_id}-read", "unit_price_usd": 0.06, "usage_unit": "1M reads"},
                "writes": {"sku_id": f"{doc_id}-write", "unit_price_usd": 0.18, "usage_unit": "1M writes"},
                "storage": {"sku_id": f"{doc_id}-storage", "unit_price_usd": 0.18, "usage_unit": "GiBy.mo"},
            },
            "formula": "database_request_based",
        }

    return _instance_doc(doc_id, name)


def seed_test_pricing_catalog(client: FakeFirestoreClient) -> None:
    for collection, names in _catalog_service_names().items():
        provider = next(key for key, value in _COLLECTION_BY_PROVIDER.items() if value == collection)
        for name in names:
            doc = _pricing_doc_for_service(name)
            client.collection(collection).document(str(doc["id"])).set(doc)
            profile_doc = build_pricing_profile_doc(provider, name)
            profile_collection = PRICING_PROFILE_COLLECTION_BY_PROVIDER[provider]
            client.collection(profile_collection).document(profile_doc["id"]).set(profile_doc)


def build_fake_firestore_with_pricing() -> FakeFirestoreClient:
    client = FakeFirestoreClient()
    seed_test_pricing_catalog(client)
    return client
