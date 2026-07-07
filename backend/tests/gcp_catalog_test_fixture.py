"""Shared fake Firestore catalog fixtures for GCP cost tests."""

from __future__ import annotations

from typing import Any

from app.pricing.gcp.catalog_lookup import GcpCatalogLookup
from app.pricing.gcp.cost_calculator import GcpCostCalculator
from app.pricing.gcp.meter_scaling import GcpMeterUnitScaler
from app.pricing.gcp.sku_roles import GcpSkuRoleResolver
from app.pricing_ingestion.models.documents import GcpCatalogRecord
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.pricing_ingestion.repositories.gcp_catalog_repository import GcpCatalogRepository
from app.utils.slug import slugify


def _sku(
    sku_id: str,
    description: str,
    usage_unit: str,
    unit_price_usd: float,
) -> dict[str, Any]:
    return {
        "sku_id": sku_id,
        "description": description,
        "usage_unit": usage_unit,
        "currency": "USD",
        "unit_price_usd": unit_price_usd,
    }


def _record(name: str, skus: dict[str, dict[str, Any]]) -> GcpCatalogRecord:
    return GcpCatalogRecord(
        id=slugify(name),
        name=name,
        skus=skus,
        formula={"total": " + ".join(f"{role}_cost" for role in skus)},
    )


_EGRESS = _sku("egress", "Data Transfer Out", "GB", 0.09)
_REQUESTS = _sku("requests", "API Requests", "Requests", 0.0000004)
_STORAGE = _sku("storage", "Storage", "GB-Mo", 0.023)
_CPU_HRS = _sku("cpu", "Compute Hours", "Hrs", 0.04048)
_MEMORY_HRS = _sku("memory", "Memory Hours", "Hrs", 0.004445)
_GB_SECONDS = _sku("cpu", "GB-Seconds", "GB-Seconds", 0.0000025)
_MEMORY_GB_SECONDS = _sku("memory", "Memory GB-Seconds", "GB-Seconds", 0.0000025)


class GcpCatalogTestFixture:
    """Seed fake Firestore with representative gcp_catalog documents."""

    def __init__(self) -> None:
        self.client = FakeFirestoreClient()
        self.repo = GcpCatalogRepository(self.client)
        self._seed_standard_catalogs()

    def _seed_standard_catalogs(self) -> None:
        records = [
            _record(
                "Cloud Run Functions",
                {
                    "requests": _sku("crf-requests", "Invocations", "Requests", 0.0000004),
                    "cpu": _GB_SECONDS,
                    "memory": _MEMORY_GB_SECONDS,
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Cloud Run",
                {
                    "cpu": _CPU_HRS,
                    "memory": _MEMORY_HRS,
                    "requests": _sku("cr-requests", "HTTP Requests", "Requests", 0.0000004),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Cloud SQL",
                {
                    "cpu": _sku("sql-instance", "Instance Hours", "Hrs", 0.017),
                    "storage": _sku("sql-storage", "Database Storage", "GB-Mo", 0.115),
                },
            ),
            _record(
                "Cloud Firestore",
                {
                    "storage": _sku("fs-storage", "Document Storage", "GB-Mo", 0.18),
                    "requests": _sku("fs-requests", "Document Operations", "Requests", 0.00000006),
                },
            ),
            _record(
                "Cloud Storage",
                {
                    "storage": _sku("gcs-storage", "Standard Storage", "GB-Mo", 0.020),
                    "requests": _sku("gcs-requests", "Class A/B Operations", "Requests", 0.0000005),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Cloud Pub/Sub",
                {
                    "requests": _sku("pubsub-ops", "Message Operations", "Requests", 0.00000004),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Cloud Tasks",
                {
                    "requests": _sku("tasks-ops", "Task Operations", "Requests", 0.0000004),
                    "storage": _sku("tasks-storage", "Task Payload Storage", "GB-Mo", 0.023),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Cloud Memorystore for Redis",
                {
                    "cpu": _sku("redis-node", "Redis Node Hours", "Hrs", 0.027),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "API Gateway",
                {
                    "requests": _sku("apigw-requests", "API Gateway Requests", "Requests", 0.000003),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Secret Manager",
                {
                    "storage": _sku("secrets-storage", "Secret Versions", "Secret-Mo", 0.06),
                    "requests": _sku("secrets-access", "Access Operations", "Requests", 0.00003),
                },
            ),
            _record(
                "Networking",
                {
                    "cpu": _sku("lb-hours", "Load Balancer Hours", "Hrs", 0.025),
                    "requests": _sku("edge-requests", "Edge Requests", "Requests", 0.00000075),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Firebase",
                {
                    "requests": _sku("firebase-requests", "Hosting/FCM Requests", "Requests", 0.0000002),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "BigQuery",
                {
                    "requests": _sku("bq-scan", "Query Data Scanned", "TB", 5.0),
                    "storage": _sku("bq-storage", "Active Storage", "GB-Mo", 0.02),
                },
            ),
            _record(
                "Cloud Logging",
                {
                    "requests": _sku("logging-ingest", "Log Ingestion", "GB", 0.50),
                    "storage": _sku("logging-storage", "Log Storage", "GB-Mo", 0.01),
                },
            ),
            _record(
                "Cloud Monitoring",
                {
                    "storage": _sku("monitoring-metrics", "Custom Metrics", "Metrics", 0.258),
                    "requests": _sku("monitoring-api", "Monitoring API Reads", "1M Requests", 0.01),
                    "cpu": _sku("monitoring-alerts", "Alert Policies", "Policies", 0.10),
                },
            ),
            _record(
                "Cloud Trace",
                {
                    "requests": _sku("trace-ingest", "Spans Ingested", "1M Traces", 0.20),
                    "memory": _sku("trace-scan", "Spans Scanned", "1M Traces", 0.50),
                },
            ),
            _record(
                "Firebase Hosting",
                {
                    "requests": _sku("hosting-requests", "Hosting Requests", "Requests", 0.0000002),
                    "egress": _EGRESS,
                },
            ),
            _record(
                "Gemini API",
                {
                    "requests": _sku("gemini-input", "Input Tokens", "1K Tokens", 0.00035),
                    "memory": _sku("gemini-output", "Output Tokens", "1K Tokens", 0.00105),
                },
            ),
            _record(
                "Vertex AI",
                {
                    "requests": _sku("vertex-input", "Input Tokens", "1K Tokens", 0.0005),
                    "memory": _sku("vertex-output", "Output Tokens", "1K Tokens", 0.0015),
                    "cpu": _sku("vertex-prediction", "Prediction Node Hours", "Hrs", 0.75),
                },
            ),
            _record(
                "Vertex AI Search",
                {
                    "requests": _sku("search-queries", "Search Queries", "Requests", 0.003),
                    "storage": _sku("search-index", "Index Storage", "GB-Mo", 0.30),
                    "egress": _EGRESS,
                },
            ),
        ]
        for record in records:
            self.repo.upsert(record)

    def build_cost_calculator(self) -> GcpCostCalculator:
        lookup = GcpCatalogLookup(self.repo)
        return GcpCostCalculator(lookup, GcpSkuRoleResolver(), GcpMeterUnitScaler())
