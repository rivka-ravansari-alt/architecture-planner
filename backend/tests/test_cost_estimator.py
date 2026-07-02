"""Tests for SKU-based cost estimation."""

from __future__ import annotations

import json

import pytest

from app.config.params import (
    COMPONENT_CATEGORY_CORE,
    FIRESTORE_COLLECTION_AWS_CATALOG,
    FIRESTORE_COLLECTION_AZURE_CATALOG,
    FIRESTORE_COLLECTION_GCP_CATALOG,
)
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.schemas.domain import MappedComponent, RequirementContext
from app.services.cost_estimator_service import CostEstimatorService
from app.utils.slug import slugify
from tests.pricing_catalog_fixtures import seed_test_pricing_catalog


@pytest.fixture
def pricing_firestore():
    client = FakeFirestoreClient()
    seed_test_pricing_catalog(client)
    return client


@pytest.fixture
def cost_estimator(pricing_firestore):
    return CostEstimatorService(firestore_client=pricing_firestore)


def _api_component() -> MappedComponent:
    return MappedComponent(
        key="api_layer",
        name="Backend / API Layer",
        component_type="api_gateway",
        reason="Central API entry point.",
        category=COMPONENT_CATEGORY_CORE,
        optional=False,
        order=10,
        cloud={
            "aws": ["API Gateway"],
            "gcp": ["Cloud Run"],
            "azure": ["API Management"],
        },
        implementation_options={},
    )


def _storage_component() -> MappedComponent:
    return MappedComponent(
        key="object_storage",
        name="Object Storage",
        component_type="object_storage",
        reason="Stores uploaded files.",
        category=COMPONENT_CATEGORY_CORE,
        optional=True,
        order=20,
        cloud={
            "aws": ["S3"],
            "gcp": ["Cloud Storage"],
            "azure": ["Blob Storage"],
        },
        implementation_options={},
    )


def test_estimates_per_component_from_firestore_skus(cost_estimator):
    components = [_api_component(), _storage_component()]
    requirements = RequirementContext(auth=True, file_upload=True)

    results = cost_estimator.estimate(
        components=components,
        expected_users="1000",
        stage="mvp",
        requirements=requirements,
    )

    assert len(results) == 3
    gcp = next(item for item in results if item.provider == "gcp")
    assert gcp.monthly_low >= 0
    assert gcp.monthly_high >= gcp.monthly_low
    assert len(gcp.component_costs) == 2

    api_estimate = next(
        item for item in gcp.component_costs if item.component_key == "api_layer"
    )
    assert api_estimate.cloud_service == "Cloud Run"
    assert len(api_estimate.matched_skus) >= 2
    assert api_estimate.confidence in {"high", "medium", "low"}
    assert api_estimate.calculation_explanation
    assert api_estimate.monthly_cost_max >= api_estimate.monthly_cost_min


def test_cloud_run_uses_multiple_skus(cost_estimator):
    components = [_api_component()]
    results = cost_estimator.estimate(
        components=components,
        expected_users="1000",
        stage="production",
        requirements=RequirementContext(),
    )
    gcp = next(item for item in results if item.provider == "gcp")
    api_estimate = gcp.component_costs[0]
    roles = {sku.role for sku in api_estimate.matched_skus}
    assert "cpu" in roles
    assert "memory" in roles


def test_free_tier_reduces_storage_cost(cost_estimator):
    components = [_storage_component()]
    results = cost_estimator.estimate(
        components=components,
        expected_users="100",
        stage="mvp",
        requirements=RequirementContext(file_upload=True),
    )
    aws = next(item for item in results if item.provider == "aws")
    storage_estimate = aws.component_costs[0]
    storage_sku = next(sku for sku in storage_estimate.matched_skus if sku.role == "storage")
    assert storage_sku.free_tier_applied > 0
    assert storage_estimate.monthly_cost_max < 5.0


def test_missing_catalog_returns_zero_with_explanation(pricing_firestore):
    estimator = CostEstimatorService(firestore_client=pricing_firestore)
    component = MappedComponent(
        key="cache",
        name="Cache",
        component_type="cache",
        reason="Caching layer.",
        category=COMPONENT_CATEGORY_CORE,
        optional=False,
        order=30,
        cloud={"aws": ["ElastiCache"], "gcp": ["Memorystore"], "azure": ["Azure Cache"]},
        implementation_options={},
    )

    results = estimator.estimate(
        components=[component],
        expected_users="1000",
        stage="mvp",
        requirements=RequirementContext(),
    )
    aws = next(item for item in results if item.provider == "aws")
    assert aws.monthly_low == 0
    assert aws.component_costs[0].missing_data
    assert "catalog" in aws.component_costs[0].missing_data[0]


def test_notes_include_component_breakdown_json(cost_estimator):
    results = cost_estimator.estimate(
        components=[_api_component()],
        expected_users="1000",
        stage="mvp",
        requirements=RequirementContext(),
    )
    payload = json.loads(results[0].notes)
    assert "component_costs" in payload
    assert payload["component_costs"][0]["matched_skus"]


def test_missing_firestore_profile_returns_low_confidence():
    client = FakeFirestoreClient()
    cloud_run = {
        "id": slugify("Cloud Run"),
        "name": "Cloud Run",
        "enabled": True,
        "skus": {
            "cpu": {
                "sku_id": "cloud-run-cpu",
                "description": "Cloud Run CPU",
                "usage_unit": "h",
                "unit_price_usd": 0.000024,
            }
        },
    }
    client.collection(FIRESTORE_COLLECTION_GCP_CATALOG).document(cloud_run["id"]).set(cloud_run)
    estimator = CostEstimatorService(firestore_client=client)

    results = estimator.estimate(
        components=[_api_component()],
        expected_users="1000",
        stage="mvp",
        requirements=RequirementContext(),
    )

    gcp = next(item for item in results if item.provider == "gcp")
    estimate = gcp.component_costs[0]
    assert estimate.confidence == "low"
    assert "missing_pricing_profile" in estimate.missing_data
    assert estimate.matched_skus == []


def test_price_realism_flags_high_storage_outlier(pricing_firestore):
    pricing_firestore.collection(FIRESTORE_COLLECTION_AZURE_CATALOG).document(
        slugify("Blob Storage")
    ).set(
        {
            "id": slugify("Blob Storage"),
            "name": "Blob Storage",
            "enabled": True,
            "skus": {
                "storage": {
                    "sku_id": "blob-storage-expensive",
                    "description": "Blob Storage LRS Data Stored",
                    "usage_unit": "GiBy.mo",
                    "unit_price_usd": 1000.0,
                }
            },
        },
        merge=True,
    )
    estimator = CostEstimatorService(firestore_client=pricing_firestore)

    results = estimator.estimate(
        components=[_storage_component()],
        expected_users="100",
        stage="mvp",
        requirements=RequirementContext(file_upload=True),
    )

    azure = next(item for item in results if item.provider == "azure")
    estimate = azure.component_costs[0]
    assert estimate.confidence == "low"
    assert "price_outlier:high:mvp_100" in estimate.missing_data
    assert "price_realism" in estimate.pricing_audit


def test_price_realism_flags_underpriced_lambda_missing_duration(pricing_firestore):
    pricing_firestore.collection(FIRESTORE_COLLECTION_AWS_CATALOG).document(
        slugify("Lambda")
    ).set(
        {
            "id": slugify("Lambda"),
            "name": "Lambda",
            "enabled": True,
            "skus": {
                "requests": {
                    "sku_id": "lambda-requests",
                    "description": "AWS Lambda requests",
                    "usage_unit": "requests",
                    "unit_price_usd": 0.0000002,
                }
            },
        }
    )
    component = MappedComponent(
        key="api",
        name="Lambda API",
        component_type="app_service",
        reason="Serverless API.",
        category=COMPONENT_CATEGORY_CORE,
        optional=False,
        order=1,
        cloud={"aws": ["Lambda"], "gcp": ["Cloud Run"], "azure": ["Functions"]},
        implementation_options={},
    )
    estimator = CostEstimatorService(firestore_client=pricing_firestore)

    results = estimator.estimate(
        components=[component],
        expected_users="1000",
        stage="mvp",
        requirements=RequirementContext(),
    )

    aws = next(item for item in results if item.provider == "aws")
    estimate = aws.component_costs[0]
    assert "missing_role:gb_seconds" in estimate.missing_data
    assert "price_outlier:low:mvp_1000" in estimate.missing_data
    assert estimate.confidence == "low"
