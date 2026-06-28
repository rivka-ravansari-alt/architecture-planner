"""Tests for Firestore-backed Azure catalog ingestion."""

from __future__ import annotations

from typing import Any

import pytest

from app.config.params import (
    FIRESTORE_COLLECTION_AZURE_CATALOG,
    FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS,
    PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS,
    PRICE_IMPORT_STATUS_FAILED,
    PRICING_PROVIDER_AZURE,
)
from app.pricing_ingestion.models.azure_catalog_ref import AzureCatalogServiceRef
from app.pricing_ingestion.normalizers.azure_catalog_normalizer import AzureCatalogNormalizer
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.pricing_ingestion.repositories.price_import_runs_repository import (
    PriceImportRunsRepository,
)
from app.pricing_ingestion.services.azure_pricing_sync_service import AzurePricingSyncService

FUNCTIONS_SERVICE = {
    "serviceId": "DZH319HJX2WX",
    "serviceName": "Functions",
    "displayName": "Functions",
}

FAILING_SERVICE = {
    "serviceId": "FAIL-SERVICE",
    "serviceName": "Failing Service",
    "displayName": "Failing Service",
}

STORAGE_SERVICE = {
    "serviceId": "DZH317F1HKN0",
    "serviceName": "Storage",
    "displayName": "Blob Storage",
}

FUNCTIONS_REF = AzureCatalogServiceRef(name="Functions", api_service_name="Functions")
FAILING_REF = AzureCatalogServiceRef(name="Failing Service", api_service_name="Failing Service")
BLOB_REF = AzureCatalogServiceRef(
    name="Blob Storage",
    api_service_name="Storage",
    price_filter="contains(productName, 'Blob')",
)

FUNCTIONS_ITEMS = [
    {
        "meterId": "exec-meter",
        "skuId": "exec-sku",
        "meterName": "Execution Count",
        "productName": "Functions",
        "unitOfMeasure": "1 Execution",
        "unitPrice": 0.0000002,
        "retailPrice": 0.0000002,
        "isPrimaryMeterRegion": True,
        "armRegionName": "eastus",
    },
    {
        "meterId": "vcpu-meter",
        "skuId": "vcpu-sku",
        "meterName": "Premium vCPU Duration",
        "productName": "Premium Functions",
        "unitOfMeasure": "1 Hour",
        "unitPrice": 0.175,
        "retailPrice": 0.175,
        "isPrimaryMeterRegion": True,
        "armRegionName": "eastus",
    },
]

STORAGE_ITEMS = [
    {
        "meterId": "blob-meter",
        "skuId": "blob-sku",
        "meterName": "LRS Data Stored",
        "productName": "Blob Storage",
        "unitOfMeasure": "1 GB/Month",
        "unitPrice": 0.018,
        "retailPrice": 0.018,
        "isPrimaryMeterRegion": True,
        "armRegionName": "eastus",
    },
]

REGISTERED_SERVICES = [FUNCTIONS_REF, FAILING_REF, BLOB_REF]


class MockAzureCatalogLoader:
    def __init__(self, services: list[AzureCatalogServiceRef] | None = None) -> None:
        self._services = services or []

    def list_enabled_services(self) -> list[AzureCatalogServiceRef]:
        return list(self._services)


class MockAzureBillingClient:
    def list_services(self, catalog_services: list[AzureCatalogServiceRef] | None = None) -> list[dict[str, Any]]:
        del catalog_services
        return [FUNCTIONS_SERVICE, FAILING_SERVICE, STORAGE_SERVICE]

    def list_skus_for_service(
        self,
        service_id: str,
        *,
        catalog_service: AzureCatalogServiceRef | None = None,
        catalog_name: str | None = None,
    ) -> list[dict[str, Any]]:
        del service_id, catalog_name
        if catalog_service is None:
            return []
        if catalog_service.name == "Failing Service":
            raise RuntimeError("billing API unavailable")
        if catalog_service.name == "Functions":
            return FUNCTIONS_ITEMS
        if catalog_service.name == "Blob Storage":
            return STORAGE_ITEMS
        return []


@pytest.fixture
def fake_firestore():
    return FakeFirestoreClient()


@pytest.fixture
def sync_service(fake_firestore):
    import_runs_repo = PriceImportRunsRepository(fake_firestore)
    azure_catalog_repo = AzureCatalogRepository(fake_firestore)
    return AzurePricingSyncService(
        billing_client=MockAzureBillingClient(),
        catalog_repo=azure_catalog_repo,
        import_runs_repo=import_runs_repo,
        service_loader=MockAzureCatalogLoader(REGISTERED_SERVICES),
    )


def test_normalizer_builds_catalog_document():
    normalizer = AzureCatalogNormalizer()
    record = normalizer.normalize_service(
        service=FUNCTIONS_SERVICE,
        skus=FUNCTIONS_ITEMS,
    )

    assert record is not None
    assert record.id == "functions"
    assert record.name == "Functions"
    assert "execution" in record.skus
    assert record.skus["execution"]["unit_price_usd"] == pytest.approx(0.0000002)
    assert "total" in record.formula


def test_sync_upserts_pricing_only_for_registered_services(sync_service, fake_firestore):
    result = sync_service.sync(triggered_by="user-1")

    assert result.provider == PRICING_PROVIDER_AZURE
    assert result.status == PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
    assert result.services_total == 3
    assert result.services_succeeded == 2
    assert result.services_failed == 1
    assert result.skus_upserted == 3

    store = fake_firestore.dump()
    assert len(store[FIRESTORE_COLLECTION_AZURE_CATALOG]) == 2
    functions = store[FIRESTORE_COLLECTION_AZURE_CATALOG]["functions"]
    assert functions["name"] == "Functions"
    assert "execution" in functions["skus"]
    assert store[FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS][result.import_run_id]["status"] == (
        PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS
    )


def test_sync_fails_when_no_enabled_services(fake_firestore):
    import_runs_repo = PriceImportRunsRepository(fake_firestore)
    azure_catalog_repo = AzureCatalogRepository(fake_firestore)
    sync_service = AzurePricingSyncService(
        billing_client=MockAzureBillingClient(),
        catalog_repo=azure_catalog_repo,
        import_runs_repo=import_runs_repo,
        service_loader=MockAzureCatalogLoader([]),
    )

    result = sync_service.sync()

    assert result.status == PRICE_IMPORT_STATUS_FAILED
    assert "No Azure service names found in the component catalog database." in result.errors[0].message
