"""SKU key mapping and free-tier pool definitions for GCP pricing."""

from __future__ import annotations

SKU_ALLOWANCE_KEYS: dict[str, dict[str, str]] = {
    "Cloud Run Functions": {
        "requests": "requests",
        "gb_seconds": "gb_seconds",
    },
    "Cloud Run": {
        "requests": "requests",
        "vcpu_hours": "vcpu_hours",
        "memory_gb_hours": "memory_gb_hours",
    },
    "Cloud Storage": {
        "storage_gb_month": "storage_gb_month",
        "requests": "requests",
    },
    "Cloud Pub/Sub": {
        "requests": "requests",
    },
    "Cloud Tasks": {
        "requests": "requests",
    },
    "Cloud SQL": {
        "instance_hours": "instance_hours",
        "storage_gb_month": "storage_gb_month",
    },
    "Cloud Firestore": {
        "storage_gb_month": "storage_gb_month",
        "read_requests": "read_requests",
        "write_requests": "write_requests",
        "delete_requests": "delete_requests",
    },
    "API Gateway": {
        "requests": "requests",
    },
    "Secret Manager": {
        "secret_months": "secret_months",
        "requests": "requests",
    },
    "Firebase": {
        "requests": "requests",
    },
    "Firebase Hosting": {
        "requests": "requests",
        "egress_gb": "egress_gb",
    },
    "BigQuery": {
        "data_scanned_tb": "data_scanned_tb",
        "storage_gb_month": "storage_gb_month",
    },
    "Cloud Logging": {
        "ingestion_gb": "ingestion_gb",
        "storage_gb_month": "storage_gb_month",
    },
    "Cloud Monitoring": {
        "custom_metrics": "custom_metrics",
        "requests": "requests",
    },
    "Cloud Trace": {
        "spans_ingested": "spans_ingested",
    },
}

FREE_TIER_POOLS: dict[str, list[str]] = {
    "gcp_cloud_run_functions_free": ["Cloud Run Functions"],
    "gcp_cloud_run_free": ["Cloud Run"],
    "gcp_cloud_storage_free": ["Cloud Storage"],
    "gcp_cloud_pubsub_free": ["Cloud Pub/Sub"],
    "gcp_cloud_tasks_free": ["Cloud Tasks"],
    "gcp_cloud_sql_free": ["Cloud SQL"],
    "gcp_cloud_firestore_free": ["Cloud Firestore"],
    "gcp_api_gateway_free": ["API Gateway"],
    "gcp_secret_manager_free": ["Secret Manager"],
    "gcp_firebase_free": ["Firebase"],
    "gcp_firebase_hosting_free": ["Firebase Hosting"],
    "gcp_bigquery_free": ["BigQuery"],
    "gcp_cloud_logging_free": ["Cloud Logging"],
    "gcp_cloud_monitoring_free": ["Cloud Monitoring"],
    "gcp_cloud_trace_free": ["Cloud Trace"],
}

POOL_FREE_TIER_ALLOWANCES: dict[str, dict[str, float]] = {
    "gcp_cloud_run_functions_free": {
        "requests": 2_000_000,
        "gb_seconds": 400_000,
    },
    "gcp_cloud_run_free": {
        "requests": 2_000_000,
    },
    "gcp_cloud_storage_free": {
        "storage_gb_month": 5,
        "requests": 50_000,
    },
    "gcp_cloud_pubsub_free": {
        "requests": 10_000_000,
    },
    "gcp_cloud_tasks_free": {
        "requests": 1_000_000,
    },
    "gcp_cloud_sql_free": {
        "instance_hours": 730,
        "storage_gb_month": 10,
    },
    "gcp_cloud_firestore_free": {
        "storage_gb_month": 1,
        "read_requests": 50_000,
        "write_requests": 20_000,
        "delete_requests": 20_000,
    },
    "gcp_api_gateway_free": {
        "requests": 2_000_000,
    },
    "gcp_secret_manager_free": {
        "secret_months": 6,
        "requests": 10_000,
    },
    "gcp_firebase_free": {
        "requests": 10_000_000,
    },
    "gcp_firebase_hosting_free": {
        "requests": 10_000_000,
        "egress_gb": 360,
    },
    "gcp_bigquery_free": {
        "data_scanned_tb": 1,
        "storage_gb_month": 10,
    },
    "gcp_cloud_logging_free": {
        "ingestion_gb": 50,
        "storage_gb_month": 30,
    },
    "gcp_cloud_monitoring_free": {
        "custom_metrics": 150,
        "requests": 1_000_000,
    },
    "gcp_cloud_trace_free": {
        "spans_ingested": 2_500_000,
    },
}

_SERVICE_TO_POOL: dict[str, str] = {
    service: pool_id
    for pool_id, services in FREE_TIER_POOLS.items()
    for service in services
}


def pool_id_for_service(service: str) -> str | None:
    return _SERVICE_TO_POOL.get(service)


def allowance_key_for_sku(service: str, sku_key: str) -> str | None:
    service_map = SKU_ALLOWANCE_KEYS.get(service, {})
    return service_map.get(sku_key)
