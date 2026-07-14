"""Seed the Firestore ``architecture_categories`` collection.

Idempotent: each category is upserted using its ``id`` as the Firestore
document id, so re-running never creates duplicates and never deletes
categories that already exist but are absent from ``CATEGORIES`` below.

Run from the backend directory:

    python scripts/seed_architecture_categories.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.firestore_client import get_firestore_client
from app.repositories.architecture_category_repository import (
    ArchitectureCategoryRepository,
)

CATEGORIES: list[dict[str, str]] = [
    {
        "id": "compute",
        "name": "Compute",
        "description": "Runs application code, APIs, containers, serverless functions, and background processing.",
    },
    {
        "id": "workflow",
        "name": "Workflow",
        "description": "Orchestrates multi-step processes, business workflows, retries, approvals, and long-running tasks.",
    },
    {
        "id": "api",
        "name": "API Gateway",
        "description": "Provides a secure entry point for APIs, handling routing, authentication, rate limiting, and request management.",
    },
    {
        "id": "authentication",
        "name": "Authentication",
        "description": "Manages user authentication, authorization, identity providers, OAuth, SSO, and access control.",
    },
    {
        "id": "sql_database",
        "name": "SQL Database",
        "description": "Stores structured relational data using tables, transactions, and SQL queries with strong consistency.",
    },
    {
        "id": "nosql_database",
        "name": "NoSQL Database",
        "description": "Stores flexible, schema-less data such as documents, key-value pairs, or wide-column records with high scalability.",
    },
    {
        "id": "storage",
        "name": "Object Storage",
        "description": "Stores files and binary objects such as images, videos, documents, backups, and generated content.",
    },
    {
        "id": "cache",
        "name": "Cache",
        "description": "Stores frequently accessed data in memory to reduce latency and improve application performance.",
    },
    {
        "id": "queue",
        "name": "Message Queue",
        "description": "Enables asynchronous communication between services by buffering and delivering messages reliably.",
    },
    {
        "id": "events",
        "name": "Event Bus",
        "description": "Distributes events between services using an event-driven architecture, allowing systems to react to changes asynchronously.",
    },
    {
        "id": "notification",
        "name": "Notification Service",
        "description": "Delivers notifications to users through channels such as email, SMS, push notifications, or in-app messaging.",
    },
    {
        "id": "scheduler",
        "name": "Scheduler",
        "description": "Runs tasks automatically at scheduled times or recurring intervals, such as cron jobs and maintenance tasks.",
    },
    {
        "id": "ai_llm",
        "name": "AI / LLM",
        "description": "Provides access to AI models for chat, text generation, summarization, image analysis, embeddings, and other intelligent features.",
    },
    {
        "id": "monitoring",
        "name": "Monitoring",
        "description": "Collects metrics, logs, traces, and health information to monitor system performance and reliability.",
    },
    {
        "id": "analytics",
        "name": "Analytics",
        "description": "Processes and analyzes application data to generate reports, dashboards, business insights, and large-scale queries.",
    },
]


def seed() -> int:
    """Upsert every category and print a created/updated/failed summary."""

    repository = ArchitectureCategoryRepository(get_firestore_client())

    created = 0
    updated = 0
    failed = 0

    for category in CATEGORIES:
        category_id = category["id"]
        try:
            was_created = repository.upsert(
                category_id=category_id,
                name=category["name"],
                description=category["description"],
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
