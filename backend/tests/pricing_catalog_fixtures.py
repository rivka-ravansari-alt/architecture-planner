"""Firestore catalog fixtures for cost estimation tests."""

from __future__ import annotations

from typing import Any

from app.config.params import (
    FIRESTORE_COLLECTION_AWS_CATALOG,
    FIRESTORE_COLLECTION_AZURE_CATALOG,
    FIRESTORE_COLLECTION_GCP_CATALOG,
    FIRESTORE_COLLECTION_PRICING_COMPONENT_PROFILES,
)
from app.services.pricing.component_profiles import iter_default_profile_documents
from app.utils.slug import slugify


def _catalog_doc(name: str, skus: dict[str, dict[str, Any]], formula: dict[str, str]) -> dict[str, Any]:
    catalog_id = slugify(name)
    return {
        "id": catalog_id,
        "name": name,
        "enabled": True,
        "skus": skus,
        "formula": formula,
    }


def _request_catalog(name: str, unit_price: float) -> dict[str, Any]:
    return _catalog_doc(
        name,
        skus={
            "requests": {
                "sku_id": f"{slugify(name)}-requests",
                "description": f"{name} requests",
                "usage_unit": "requests",
                "unit_price_usd": unit_price,
            }
        },
        formula={
            "requests_cost": "monthly_requests * skus.requests.unit_price_usd",
            "total": "requests_cost",
        },
    )


def _storage_catalog(name: str, unit_price: float, *, free_tier: float | None = None) -> dict[str, Any]:
    sku: dict[str, Any] = {
        "sku_id": f"{slugify(name)}-storage",
        "description": f"{name} storage",
        "usage_unit": "GiBy.mo",
        "unit_price_usd": unit_price,
    }
    if free_tier is not None:
        sku["free_tier_amount"] = free_tier
    return _catalog_doc(
        name,
        skus={"storage": sku},
        formula={
            "storage_cost": "storage_gib * skus.storage.unit_price_usd",
            "total": "storage_cost",
        },
    )


def _hosting_catalog(name: str) -> dict[str, Any]:
    return _catalog_doc(
        name,
        skus={
            "requests": {
                "sku_id": f"{slugify(name)}-requests",
                "description": f"{name} requests",
                "usage_unit": "requests",
                "unit_price_usd": 0.0000004,
            },
            "storage": {
                "sku_id": f"{slugify(name)}-storage",
                "description": f"{name} storage",
                "usage_unit": "GiBy.mo",
                "unit_price_usd": 0.026,
                "free_tier_amount": 10.0,
            },
        },
        formula={
            "requests_cost": "monthly_requests * skus.requests.unit_price_usd",
            "storage_cost": "storage_gib * skus.storage.unit_price_usd",
            "total": "requests_cost + storage_cost",
        },
    )


def _cloud_run_catalog() -> dict[str, Any]:
    return _catalog_doc(
        "Cloud Run",
        skus={
            "cpu": {
                "sku_id": "cloud-run-cpu",
                "description": "Cloud Run CPU",
                "usage_unit": "h",
                "unit_price_usd": 0.000024,
            },
            "memory": {
                "sku_id": "cloud-run-memory",
                "description": "Cloud Run Memory",
                "usage_unit": "GiBy.h",
                "unit_price_usd": 0.0000025,
            },
            "requests": {
                "sku_id": "cloud-run-requests",
                "description": "Cloud Run requests",
                "usage_unit": "requests",
                "unit_price_usd": 0.40,
                "free_tier_amount": 2_000_000,
            },
        },
        formula={
            "cpu_cost": "monthly_requests * avg_request_duration * cpu * skus.cpu.unit_price_usd",
            "memory_cost": (
                "monthly_requests * avg_request_duration * memory_gib * skus.memory.unit_price_usd"
            ),
            "request_cost": "(monthly_requests / 1000000) * skus.requests.unit_price_usd",
            "total": "cpu_cost + memory_cost + request_cost",
        },
    )


def seed_test_pricing_catalog(client: Any) -> None:
    aws_catalogs = [
        _hosting_catalog("Amplify Hosting"),
        _request_catalog("API Gateway", 0.0000035),
        _request_catalog("Cognito", 0.0000055),
        _storage_catalog("S3", 0.023, free_tier=5.0),
    ]
    gcp_catalogs = [
        _hosting_catalog("Firebase Hosting"),
        _request_catalog("API Gateway", 0.000003),
        _request_catalog("Firebase Authentication", 0.0),
        _storage_catalog("Cloud Storage", 0.020, free_tier=5.0),
        _cloud_run_catalog(),
    ]
    azure_catalogs = [
        _hosting_catalog("Azure App Service"),
        _request_catalog("API Management", 0.000004),
        _request_catalog("Entra ID B2C", 0.000003),
        _storage_catalog("Blob Storage", 0.018, free_tier=5.0),
    ]

    for doc in aws_catalogs:
        client.collection(FIRESTORE_COLLECTION_AWS_CATALOG).document(doc["id"]).set(doc)
    for doc in gcp_catalogs:
        client.collection(FIRESTORE_COLLECTION_GCP_CATALOG).document(doc["id"]).set(doc)
    for doc in azure_catalogs:
        client.collection(FIRESTORE_COLLECTION_AZURE_CATALOG).document(doc["id"]).set(doc)
    for doc in iter_default_profile_documents():
        client.collection(FIRESTORE_COLLECTION_PRICING_COMPONENT_PROFILES).document(doc["id"]).set(doc)
