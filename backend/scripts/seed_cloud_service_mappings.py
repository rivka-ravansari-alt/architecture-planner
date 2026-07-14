"""Seed the Firestore ``cloud_service_mappings`` collection.

Idempotent: each mapping is upserted using its ``category_id`` as the Firestore
document id, so re-running never creates duplicates and never deletes mappings
that already exist but are absent from ``MAPPINGS`` below.

Run from the backend directory:

    python scripts/seed_cloud_service_mappings.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.firestore_client import get_firestore_client
from app.repositories.cloud_service_mapping_repository import (
    CloudServiceMappingRepository,
)

MAPPINGS: list[dict] = [
    {
        "category_id": "compute",
        "providers": {
            "aws": [
                {"service_id": "aws_lambda", "priority": 1, "service_type": "serverless_function"},
                {"service_id": "aws_fargate", "priority": 2, "service_type": "serverless_container"},
                {"service_id": "aws_app_runner", "priority": 3, "service_type": "managed_container"},
                {"service_id": "aws_ec2", "priority": 4, "service_type": "virtual_machine"},
            ],
            "gcp": [
                {"service_id": "gcp_cloud_functions", "priority": 1, "service_type": "serverless_function"},
                {"service_id": "gcp_cloud_run", "priority": 2, "service_type": "serverless_container"},
                {"service_id": "gcp_compute_engine", "priority": 3, "service_type": "virtual_machine"},
            ],
            "azure": [
                {"service_id": "azure_functions", "priority": 1, "service_type": "serverless_function"},
                {"service_id": "azure_container_apps", "priority": 2, "service_type": "serverless_container"},
                {"service_id": "azure_virtual_machines", "priority": 3, "service_type": "virtual_machine"},
            ],
        },
    },
    {
        "category_id": "workflow",
        "providers": {
            "aws": [{"service_id": "aws_step_functions", "priority": 1}],
            "gcp": [{"service_id": "gcp_workflows", "priority": 1}],
            "azure": [{"service_id": "azure_logic_apps", "priority": 1}],
        },
    },
    {
        "category_id": "api",
        "providers": {
            "aws": [{"service_id": "aws_api_gateway", "priority": 1}],
            "gcp": [{"service_id": "gcp_api_gateway", "priority": 1}],
            "azure": [{"service_id": "azure_api_management", "priority": 1}],
        },
    },
    {
        "category_id": "authentication",
        "providers": {
            "aws": [{"service_id": "aws_cognito", "priority": 1}],
            "gcp": [{"service_id": "gcp_firebase_auth", "priority": 1}],
            "azure": [{"service_id": "azure_entra_id", "priority": 1}],
        },
    },
    {
        "category_id": "sql_database",
        "providers": {
            "aws": [
                {"service_id": "aws_rds", "priority": 1},
                {"service_id": "aws_aurora", "priority": 2},
            ],
            "gcp": [
                {"service_id": "gcp_cloud_sql", "priority": 1},
                {"service_id": "gcp_alloydb", "priority": 2},
            ],
            "azure": [
                {"service_id": "azure_sql_database", "priority": 1},
                {"service_id": "azure_postgresql", "priority": 2},
                {"service_id": "azure_mysql", "priority": 3},
            ],
        },
    },
    {
        "category_id": "nosql_database",
        "providers": {
            "aws": [{"service_id": "aws_dynamodb", "priority": 1}],
            "gcp": [{"service_id": "gcp_firestore", "priority": 1}],
            "azure": [{"service_id": "azure_cosmos_db", "priority": 1}],
        },
    },
    {
        "category_id": "storage",
        "providers": {
            "aws": [{"service_id": "aws_s3", "priority": 1}],
            "gcp": [{"service_id": "gcp_cloud_storage", "priority": 1}],
            "azure": [{"service_id": "azure_blob_storage", "priority": 1}],
        },
    },
    {
        "category_id": "cache",
        "providers": {
            "aws": [
                {"service_id": "aws_elasticache_redis", "priority": 1},
                {"service_id": "aws_elasticache_valkey", "priority": 2},
                {"service_id": "aws_elasticache_memcached", "priority": 3},
            ],
            "gcp": [{"service_id": "gcp_memorystore_redis", "priority": 1}],
            "azure": [{"service_id": "azure_cache_for_redis", "priority": 1}],
        },
    },
    {
        "category_id": "queue",
        "providers": {
            "aws": [{"service_id": "aws_sqs", "priority": 1}],
            "gcp": [{"service_id": "gcp_pubsub", "priority": 1}],
            "azure": [
                {"service_id": "azure_service_bus", "priority": 1},
                {"service_id": "azure_queue_storage", "priority": 2},
            ],
        },
    },
    {
        "category_id": "events",
        "providers": {
            "aws": [{"service_id": "aws_eventbridge", "priority": 1}],
            "gcp": [{"service_id": "gcp_eventarc", "priority": 1}],
            "azure": [{"service_id": "azure_event_grid", "priority": 1}],
        },
    },
    {
        "category_id": "notification",
        "providers": {
            "aws": [
                {"service_id": "aws_sns", "priority": 1},
                {"service_id": "aws_ses", "priority": 2},
            ],
            "gcp": [{"service_id": "gcp_firebase_messaging", "priority": 1}],
            "azure": [{"service_id": "azure_notification_hubs", "priority": 1}],
        },
    },
    {
        "category_id": "scheduler",
        "providers": {
            "aws": [{"service_id": "aws_eventbridge_scheduler", "priority": 1}],
            "gcp": [{"service_id": "gcp_cloud_scheduler", "priority": 1}],
            "azure": [{"service_id": "azure_logic_apps_scheduler", "priority": 1}],
        },
    },
    {
        "category_id": "ai_llm",
        "providers": {
            "aws": [{"service_id": "aws_bedrock", "priority": 1}],
            "gcp": [{"service_id": "gcp_vertex_ai", "priority": 1}],
            "azure": [{"service_id": "azure_ai_foundry", "priority": 1}],
        },
    },
    {
        "category_id": "monitoring",
        "providers": {
            "aws": [{"service_id": "aws_cloudwatch", "priority": 1}],
            "gcp": [{"service_id": "gcp_cloud_monitoring", "priority": 1}],
            "azure": [{"service_id": "azure_monitor", "priority": 1}],
        },
    },
    {
        "category_id": "analytics",
        "providers": {
            "aws": [{"service_id": "aws_redshift", "priority": 1}],
            "gcp": [{"service_id": "gcp_bigquery", "priority": 1}],
            "azure": [{"service_id": "azure_synapse", "priority": 1}],
        },
    },
]


def seed() -> int:
    """Upsert every mapping and print a created/updated/failed summary."""

    repository = CloudServiceMappingRepository(get_firestore_client())

    created = 0
    updated = 0
    failed = 0

    for mapping in MAPPINGS:
        category_id = mapping["category_id"]
        try:
            was_created = repository.upsert(
                category_id=category_id,
                providers=mapping["providers"],
            )
        except Exception as error:  # noqa: BLE001 - report and continue seeding
            failed += 1
            print(f"Failed to upsert '{category_id}': {error}")
            continue

        if was_created:
            created += 1
        else:
            updated += 1

    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(seed())
