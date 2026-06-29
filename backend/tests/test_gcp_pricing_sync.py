"""Tests for Firestore-backed GCP catalog ingestion and multi-cloud sync routing."""

from __future__ import annotations

from typing import Any

import pytest

from app.config.params import (
    FIRESTORE_COLLECTION_GCP_CATALOG,
    FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS,
    PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS,
    PRICE_IMPORT_STATUS_FAILED,
    PRICING_PROVIDER_AWS,
    PRICING_PROVIDER_AZURE,
    PRICING_PROVIDER_GCP,
)
from app.pricing_ingestion.clients.aws_billing_client import AwsBillingClient
from app.pricing_ingestion.clients.azure_billing_client import AzureBillingClient
from app.pricing_ingestion.normalizers.gcp_catalog_normalizer import GcpCatalogNormalizer
from app.pricing_ingestion.providers.registry import PricingSyncRegistry
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.models.aws_catalog_ref import AwsCatalogServiceRef
from app.pricing_ingestion.models.azure_catalog_ref import AzureCatalogServiceRef
from app.pricing_ingestion.services.aws_pricing_sync_service import AwsPricingSyncService
from app.pricing_ingestion.services.azure_pricing_sync_service import AzurePricingSyncService
from app.pricing_ingestion.services.db_azure_catalog_loader import DbAzureCatalogLoader
from app.pricing_ingestion.services.firestore_gcp_catalog_loader import FirestoreGcpCatalogLoader
from app.pricing_ingestion.services.gcp_pricing_sync_service import GcpPricingSyncService



def _unit_price(units: int = 0, nanos: int = 0) -> dict[str, Any]:
    return {"currencyCode": "USD", "units": str(units), "nanos": nanos}


def _pricing_info(usage_unit: str, units: int, nanos: int) -> dict[str, Any]:
    return {
        "pricingExpression": {
            "usageUnit": usage_unit,
            "baseUnit": usage_unit,
            "tieredRates": [{"unitPrice": _unit_price(units, nanos)}],
        }
    }


CLOUD_RUN_SERVICE = {
    "serviceId": "152E-C115-5142",
    "displayName": "Cloud Run",
}

FAILING_SERVICE = {
    "serviceId": "FAIL-SERVICE",
    "displayName": "Failing Service",
}

GENERIC_SERVICE = {
    "serviceId": "TEST-SERVICE-01",
    "displayName": "Test Compute",
}

CLOUD_RUN_SKUS = [
    {
        "skuId": "cpu-sku",
        "description": "Cloud Run CPU",
        "category": {"resourceFamily": "Compute", "resourceGroup": "CPU", "usageType": "OnDemand"},
        "pricingInfo": [_pricing_info("h", 0, 24000)],
    },
    {
        "skuId": "memory-sku",
        "description": "Cloud Run Memory",
        "category": {"resourceFamily": "Compute", "resourceGroup": "RAM", "usageType": "OnDemand"},
        "pricingInfo": [_pricing_info("GiBy.h", 0, 2500000)],
    },
]

GENERIC_SKUS = [
    {
        "skuId": "generic-sku",
        "description": "Test usage",
        "category": {"resourceFamily": "Compute", "resourceGroup": "Cores", "usageType": "OnDemand"},
        "pricingInfo": [_pricing_info("h", 1, 500000000)],
    },
]

REGISTERED_SERVICE_NAMES = ["Cloud Run", "Failing Service", "Test Compute"]


class MockGcpBillingClient:
    def list_services(self) -> list[dict[str, Any]]:
        return [CLOUD_RUN_SERVICE, FAILING_SERVICE, GENERIC_SERVICE]

    def list_skus_for_service(self, service_id: str) -> list[dict[str, Any]]:
        if service_id == "FAIL-SERVICE":
            raise RuntimeError("billing API unavailable")
        if service_id == "152E-C115-5142":
            return CLOUD_RUN_SKUS
        return GENERIC_SKUS


class MockAwsCatalogLoader:
    def __init__(self, services: list[AwsCatalogServiceRef] | None = None) -> None:
        self._services = services or []

    def list_enabled_services(self) -> list[AwsCatalogServiceRef]:
        return list(self._services)


class MockAzureCatalogLoader:
    def __init__(self, services: list[AzureCatalogServiceRef] | None = None) -> None:
        self._services = services or []

    def list_enabled_services(self) -> list[AzureCatalogServiceRef]:
        return list(self._services)


def _build_registry(
    fake_firestore: FakeFirestoreClient,
    *,
    azure_services: list[AzureCatalogServiceRef] | None = None,
    aws_services: list[AwsCatalogServiceRef] | None = None,
) -> PricingSyncRegistry:
    import_runs_repo = PriceImportRunsRepository(fake_firestore)
    gcp_catalog_repo = GcpCatalogRepository(fake_firestore)
    return PricingSyncRegistry(
        {
            PRICING_PROVIDER_GCP: GcpPricingSyncService(
                billing_client=MockGcpBillingClient(),
                catalog_repo=gcp_catalog_repo,
                import_runs_repo=import_runs_repo,
                service_loader=FirestoreGcpCatalogLoader(gcp_catalog_repo),
            ),
            PRICING_PROVIDER_AWS: AwsPricingSyncService(
                billing_client=AwsBillingClient(),
                catalog_repo=AwsCatalogRepository(fake_firestore),
                import_runs_repo=import_runs_repo,
                service_loader=MockAwsCatalogLoader(aws_services),
            ),
            PRICING_PROVIDER_AZURE: AzurePricingSyncService(
                billing_client=AzureBillingClient(),
                catalog_repo=AzureCatalogRepository(fake_firestore),
                import_runs_repo=import_runs_repo,
                service_loader=MockAzureCatalogLoader(azure_services),
            ),
        }
    )


@pytest.fixture
def fake_firestore():
    client = FakeFirestoreClient()
    client.seed_gcp_catalog_names(REGISTERED_SERVICE_NAMES)
    return client


@pytest.fixture
def sync_service(fake_firestore):
    return _build_registry(fake_firestore).get(PRICING_PROVIDER_GCP)


def test_normalizer_builds_catalog_document():
    normalizer = GcpCatalogNormalizer()
    record = normalizer.normalize_service(
        service=CLOUD_RUN_SERVICE,
        skus=CLOUD_RUN_SKUS,
    )

    assert record is not None
    assert record.id == "cloud_run"
    assert record.name == "Cloud Run"
    assert record.formula["total"] == "cpu_cost + memory_cost + request_cost"
    assert "skus.cpu.unit_price_usd" in record.formula["cpu_cost"]
    assert set(record.skus.keys()) == {"cpu", "memory"}
    assert record.skus["cpu"]["unit_price_usd"] == pytest.approx(0.000024)


def test_sync_upserts_pricing_only_for_registered_services(sync_service, fake_firestore):
    result = sync_service.sync(triggered_by="user-1")

    assert result.provider == PRICING_PROVIDER_GCP
    assert result.status == PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
    assert result.services_total == 3
    assert result.services_succeeded == 2
    assert result.services_failed == 1
    assert result.skus_upserted == 3

    store = fake_firestore.dump()
    assert len(store[FIRESTORE_COLLECTION_GCP_CATALOG]) == 3
    cloud_run = store[FIRESTORE_COLLECTION_GCP_CATALOG]["cloud_run"]
    assert cloud_run["id"] == "cloud_run"
    assert cloud_run["name"] == "Cloud Run"
    assert cloud_run["formula"]["total"] == "cpu_cost + memory_cost + request_cost"
    assert "cpu" in cloud_run["skus"]
    assert store[FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS][result.import_run_id]["status"] == (
        PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
    )


def test_sync_is_idempotent_for_catalog_documents(sync_service, fake_firestore):
    first = sync_service.sync()
    second = sync_service.sync()

    assert first.skus_upserted == second.skus_upserted
    assert len(fake_firestore.dump()[FIRESTORE_COLLECTION_GCP_CATALOG]) == 3


def test_aws_sync_fails_without_registered_services(fake_firestore):
    result = _build_registry(fake_firestore, aws_services=[]).get(PRICING_PROVIDER_AWS).sync()

    assert result.provider == PRICING_PROVIDER_AWS
    assert result.status == PRICE_IMPORT_STATUS_FAILED
    assert "No AWS service names found in the component catalog database." in result.errors[0].message


def test_azure_sync_fails_without_registered_services(fake_firestore):
    result = _build_registry(fake_firestore, azure_services=[]).get(PRICING_PROVIDER_AZURE).sync()

    assert result.provider == PRICING_PROVIDER_AZURE
    assert result.status == PRICE_IMPORT_STATUS_FAILED
    assert "No Azure service names found in the component catalog database." in result.errors[0].message
