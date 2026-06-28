"""Tests for Firestore-backed AWS catalog ingestion."""

from __future__ import annotations

from typing import Any

import pytest

from app.config.params import (
    FIRESTORE_COLLECTION_AWS_CATALOG,
    FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS,
    PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS,
    PRICE_IMPORT_STATUS_FAILED,
    PRICING_PROVIDER_AWS,
)
from app.pricing_ingestion.models.aws_catalog_ref import AwsCatalogServiceRef
from app.pricing_ingestion.normalizers.aws_catalog_normalizer import AwsCatalogNormalizer
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.services.aws_pricing_sync_service import AwsPricingSyncService

LAMBDA_SERVICE = {
    "serviceId": "AWSLambda",
    "serviceCode": "AWSLambda",
    "displayName": "Lambda",
}

FAILING_SERVICE = {
    "serviceId": "FAIL-SERVICE",
    "serviceCode": "FAIL-SERVICE",
    "displayName": "Failing Service",
}

S3_SERVICE = {
    "serviceId": "AmazonS3",
    "serviceCode": "AmazonS3",
    "displayName": "S3",
}

LAMBDA_REF = AwsCatalogServiceRef(name="Lambda", api_service_code="AWSLambda")
FAILING_REF = AwsCatalogServiceRef(name="Failing Service", api_service_code="FAIL-SERVICE")
S3_REF = AwsCatalogServiceRef(name="S3", api_service_code="AmazonS3")

LAMBDA_ITEMS = [
    {
        "sku": "lambda-request",
        "productFamily": "Serverless",
        "attributes": {
            "group": "AWS-Lambda-Requests",
            "regionCode": "us-east-1",
            "usagetype": "Lambda-Requests-Tier1",
        },
        "priceDimension": {
            "description": "AWS Lambda - Requests - US East (Northern Virginia)",
            "unit": "Requests",
            "pricePerUnit": {"USD": "0.0000002000"},
        },
        "effectiveDate": "2026-06-01T00:00:00Z",
    },
    {
        "sku": "lambda-duration",
        "productFamily": "Serverless",
        "attributes": {
            "group": "AWS-Lambda-Duration",
            "regionCode": "us-east-1",
            "usagetype": "Lambda-GB-Second",
        },
        "priceDimension": {
            "description": "AWS Lambda - Total Compute - US East (Northern Virginia)-Tier-1",
            "unit": "GB-Seconds",
            "pricePerUnit": {"USD": "0.0000166667"},
        },
        "effectiveDate": "2026-06-01T00:00:00Z",
    },
]

S3_ITEMS = [
    {
        "sku": "s3-storage",
        "productFamily": "Storage",
        "attributes": {
            "group": "S3-Storage",
            "regionCode": "us-east-1",
            "usagetype": "TimedStorage-ByteHrs",
        },
        "priceDimension": {
            "description": "Amazon S3 Standard storage",
            "unit": "GB-Mo",
            "pricePerUnit": {"USD": "0.0230000000"},
        },
        "effectiveDate": "2026-06-01T00:00:00Z",
    },
]

REGISTERED_SERVICES = [LAMBDA_REF, FAILING_REF, S3_REF]


class MockAwsCatalogLoader:
    def __init__(self, services: list[AwsCatalogServiceRef] | None = None) -> None:
        self._services = services or []

    def list_enabled_services(self) -> list[AwsCatalogServiceRef]:
        return list(self._services)


class MockAwsBillingClient:
    def list_services(
        self,
        catalog_services: list[AwsCatalogServiceRef] | None = None,
    ) -> list[dict[str, Any]]:
        del catalog_services
        return [LAMBDA_SERVICE, FAILING_SERVICE, S3_SERVICE]

    def list_skus_for_service(
        self,
        service_id: str,
        *,
        catalog_service: AwsCatalogServiceRef | None = None,
    ) -> list[dict[str, Any]]:
        del service_id
        if catalog_service is None:
            return []
        if catalog_service.name == "Failing Service":
            raise RuntimeError("billing API unavailable")
        if catalog_service.name == "Lambda":
            return LAMBDA_ITEMS
        if catalog_service.name == "S3":
            return S3_ITEMS
        return []


@pytest.fixture
def fake_firestore():
    return FakeFirestoreClient()


@pytest.fixture
def sync_service(fake_firestore):
    import_runs_repo = PriceImportRunsRepository(fake_firestore)
    aws_catalog_repo = AwsCatalogRepository(fake_firestore)
    return AwsPricingSyncService(
        billing_client=MockAwsBillingClient(),
        catalog_repo=aws_catalog_repo,
        import_runs_repo=import_runs_repo,
        service_loader=MockAwsCatalogLoader(REGISTERED_SERVICES),
    )


def test_normalizer_builds_catalog_document():
    normalizer = AwsCatalogNormalizer()
    record = normalizer.normalize_service(service=LAMBDA_SERVICE, skus=LAMBDA_ITEMS)

    assert record is not None
    assert record.id == "lambda"
    assert record.name == "Lambda"
    assert "requests" in record.skus
    assert record.skus["requests"]["unit_price_usd"] == pytest.approx(0.0000002)
    assert "total" in record.formula


def test_sync_upserts_pricing_for_registered_services(sync_service, fake_firestore):
    result = sync_service.sync(triggered_by="user-1")

    assert result.provider == PRICING_PROVIDER_AWS
    assert result.status == PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
    assert result.services_total == 3
    assert result.services_succeeded == 2
    assert result.services_failed == 1
    assert result.skus_upserted == 3

    store = fake_firestore.dump()
    assert len(store[FIRESTORE_COLLECTION_AWS_CATALOG]) == 2
    lambda_doc = store[FIRESTORE_COLLECTION_AWS_CATALOG]["lambda"]
    assert lambda_doc["name"] == "Lambda"
    assert "requests" in lambda_doc["skus"]
    assert store[FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS][result.import_run_id]["status"] == (
        PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
    )


def test_sync_fails_when_no_enabled_services(fake_firestore):
    sync_service = AwsPricingSyncService(
        billing_client=MockAwsBillingClient(),
        catalog_repo=AwsCatalogRepository(fake_firestore),
        import_runs_repo=PriceImportRunsRepository(fake_firestore),
        service_loader=MockAwsCatalogLoader([]),
    )

    result = sync_service.sync()

    assert result.status == PRICE_IMPORT_STATUS_FAILED
    assert "No AWS service names found in the component catalog database." in result.errors[0].message
