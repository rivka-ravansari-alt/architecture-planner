"""Shared fake Firestore catalog fixtures for Azure cost tests."""

from __future__ import annotations

from app.pricing.azure.catalog_lookup import AzureCatalogLookup
from app.pricing.azure.cost_calculator import AzureCostCalculator
from app.pricing.azure.meter_scaling import MeterUnitScaler
from app.pricing.azure.sku_roles import SkuRoleResolver
from app.pricing_ingestion.models.documents import AzureCatalogRecord
from app.pricing_ingestion.normalizers.azure_catalog_normalizer import AzureCatalogNormalizer
from app.pricing_ingestion.repositories.azure_catalog_repository import AzureCatalogRepository
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.utils.slug import slugify
from tests.test_azure_pricing_sync import (
    BLOB_REF,
    FUNCTIONS_ITEMS,
    FUNCTIONS_REF,
    FUNCTIONS_SERVICE,
    STORAGE_ITEMS,
    STORAGE_SERVICE,
)


class AzureCatalogTestFixture:
    """Seed fake Firestore with representative azure_catalog documents."""

    def __init__(self) -> None:
        self.client = FakeFirestoreClient()
        self.repo = AzureCatalogRepository(self.client)
        self.normalizer = AzureCatalogNormalizer()
        self._seed_standard_catalogs()

    def _seed_standard_catalogs(self) -> None:
        functions_record = self.normalizer.normalize_service(
            service=FUNCTIONS_SERVICE,
            skus=FUNCTIONS_ITEMS
            + [
                {
                    "meterId": "mem-meter",
                    "skuId": "mem-sku",
                    "meterName": "Memory Duration",
                    "productName": "Functions",
                    "unitOfMeasure": "1 GB Second",
                    "unitPrice": 0.000001,
                    "retailPrice": 0.000001,
                    "isPrimaryMeterRegion": True,
                    "armRegionName": "eastus",
                },
                {
                    "meterId": "fn-egress-meter",
                    "skuId": "fn-egress-sku",
                    "meterName": "Data Transfer Out",
                    "productName": "Functions",
                    "unitOfMeasure": "1 GB",
                    "unitPrice": 0.09,
                    "retailPrice": 0.09,
                    "isPrimaryMeterRegion": True,
                    "armRegionName": "eastus",
                },
                {
                    "meterId": "fn-cpu-meter",
                    "skuId": "fn-cpu-sku",
                    "meterName": "Premium vCPU Duration",
                    "productName": "Functions",
                    "unitOfMeasure": "1 Hour",
                    "unitPrice": 0.173,
                    "retailPrice": 0.173,
                    "isPrimaryMeterRegion": True,
                    "armRegionName": "eastus",
                },
            ],
        )
        blob_record = self.normalizer.normalize_service(
            service=STORAGE_SERVICE,
            skus=STORAGE_ITEMS,
        )
        assert functions_record is not None
        assert blob_record is not None
        self.repo.upsert(functions_record)
        blob_with_writes = AzureCatalogRecord(
            id=blob_record.id,
            name=blob_record.name,
            skus={
                **blob_record.skus,
                "storage:hot:lrs": dict(blob_record.skus.get("storage", {})),
                "requests": {
                    "sku_id": "write-sku",
                    "meter_id": "write-meter",
                    "description": "Write Operations",
                    "usage_unit": "10 K",
                    "product_name": "Blob Storage",
                    "currency": "USD",
                    "unit_price_usd": 0.05,
                },
                "egress": {
                    "sku_id": "blob-egress",
                    "meter_id": "blob-egress-meter",
                    "description": "Data Egress",
                    "usage_unit": "1 GB",
                    "product_name": "Blob Storage",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula=blob_record.formula,
        )
        self.repo.upsert(blob_with_writes)

        container_apps = AzureCatalogRecord(
            id=slugify("Azure Container Apps"),
            name="Azure Container Apps",
            skus={
                "cpu": {
                    "sku_id": "ca-cpu",
                    "meter_id": "ca-cpu-meter",
                    "description": "vCPU Seconds",
                    "usage_unit": "1 vCPU Second",
                    "product_name": "Container Apps",
                    "currency": "USD",
                    "unit_price_usd": 0.000012,
                },
                "memory": {
                    "sku_id": "ca-mem",
                    "meter_id": "ca-mem-meter",
                    "description": "Memory GiB Seconds",
                    "usage_unit": "1 GiB Second",
                    "product_name": "Container Apps",
                    "currency": "USD",
                    "unit_price_usd": 0.000001,
                },
                "requests": {
                    "sku_id": "ca-req",
                    "meter_id": "ca-req-meter",
                    "description": "Requests",
                    "usage_unit": "1 Request",
                    "product_name": "Container Apps",
                    "currency": "USD",
                    "unit_price_usd": 0.0000004,
                },
                "egress": {
                    "sku_id": "ca-egress",
                    "meter_id": "ca-egress-meter",
                    "description": "Data Egress",
                    "usage_unit": "1 GB",
                    "product_name": "Container Apps",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "cpu_cost + requests_cost"},
        )
        sql_db = AzureCatalogRecord(
            id=slugify("SQL Database"),
            name="SQL Database",
            skus={
                "storage": {
                    "sku_id": "sql-storage",
                    "meter_id": "sql-storage-meter",
                    "description": "Storage",
                    "usage_unit": "1 GB/Month",
                    "product_name": "SQL Database",
                    "currency": "USD",
                    "unit_price_usd": 0.115,
                },
                "storage:hot:lrs": {
                    "sku_id": "sql-storage-hot",
                    "meter_id": "sql-storage-hot-meter",
                    "description": "Storage Hot LRS",
                    "usage_unit": "1 GB/Month",
                    "product_name": "SQL Database",
                    "currency": "USD",
                    "unit_price_usd": 0.115,
                },
                "instance": {
                    "sku_id": "sql-instance",
                    "meter_id": "sql-instance-meter",
                    "description": "Standard S1 DTU Database",
                    "usage_unit": "1/month",
                    "product_name": "SQL Database",
                    "currency": "USD",
                    "unit_price_usd": 30.0,
                },
                "instance:standard_s1": {
                    "sku_id": "sql-instance-s1",
                    "meter_id": "sql-instance-s1-meter",
                    "description": "Standard S1",
                    "usage_unit": "1/month",
                    "product_name": "SQL Database",
                    "currency": "USD",
                    "unit_price_usd": 30.0,
                },
            },
            formula={"total": "storage_cost + instance_cost"},
        )
        service_bus = AzureCatalogRecord(
            id=slugify("Service Bus"),
            name="Service Bus",
            skus={
                "queue": {
                    "sku_id": "sb-queue",
                    "meter_id": "sb-queue-meter",
                    "description": "Operations",
                    "usage_unit": "1M",
                    "product_name": "Service Bus",
                    "currency": "USD",
                    "unit_price_usd": 0.05,
                },
                "namespace": {
                    "sku_id": "sb-namespace",
                    "meter_id": "sb-namespace-meter",
                    "description": "Standard Base Unit",
                    "usage_unit": "1/month",
                    "product_name": "Service Bus",
                    "currency": "USD",
                    "unit_price_usd": 10.0,
                },
                "namespace:standard": {
                    "sku_id": "sb-namespace-std",
                    "meter_id": "sb-namespace-std-meter",
                    "description": "Standard Namespace",
                    "usage_unit": "1/month",
                    "product_name": "Service Bus",
                    "currency": "USD",
                    "unit_price_usd": 10.0,
                },
                "requests": {
                    "sku_id": "sb-connections",
                    "meter_id": "sb-connections-meter",
                    "description": "Brokered Connections",
                    "usage_unit": "1 Connection",
                    "product_name": "Service Bus",
                    "currency": "USD",
                    "unit_price_usd": 0.05,
                },
                "egress": {
                    "sku_id": "sb-egress",
                    "meter_id": "sb-egress-meter",
                    "description": "Data Egress",
                    "usage_unit": "1 GB",
                    "product_name": "Service Bus",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
                "cpu": {
                    "sku_id": "sb-mu",
                    "meter_id": "sb-mu-meter",
                    "description": "Premium Messaging Unit",
                    "usage_unit": "1 Hour",
                    "product_name": "Service Bus",
                    "currency": "USD",
                    "unit_price_usd": 0.928,
                },
            },
            formula={"total": "queue_cost + namespace_cost"},
        )
        queue_storage = AzureCatalogRecord(
            id=slugify("Queue Storage"),
            name="Queue Storage",
            skus={
                "storage": {
                    "sku_id": "queue-storage",
                    "meter_id": "queue-storage-meter",
                    "description": "Queue Data Stored",
                    "usage_unit": "1 GB/Month",
                    "product_name": "Queue Storage",
                    "currency": "USD",
                    "unit_price_usd": 0.018,
                },
                "queue": {
                    "sku_id": "queue-ops",
                    "meter_id": "queue-ops-meter",
                    "description": "Queue Operations",
                    "usage_unit": "10 K",
                    "product_name": "Queue Storage",
                    "currency": "USD",
                    "unit_price_usd": 0.004,
                },
                "egress": {
                    "sku_id": "queue-egress",
                    "meter_id": "queue-egress-meter",
                    "description": "Data Egress",
                    "usage_unit": "1 GB",
                    "product_name": "Queue Storage",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "storage_cost + queue_cost"},
        )
        self.repo.upsert(container_apps)
        self.repo.upsert(sql_db)
        self.repo.upsert(service_bus)
        self.repo.upsert(queue_storage)

    def build_cost_calculator(self) -> AzureCostCalculator:
        lookup = AzureCatalogLookup(self.repo)
        return AzureCostCalculator(lookup, SkuRoleResolver(), MeterUnitScaler())
