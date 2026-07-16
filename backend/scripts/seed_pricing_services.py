"""Seed the Firestore ``pricing_services`` collection.

Idempotent: each document is upserted using its ``service_id`` as the Firestore
document id, so re-running never creates duplicates and never deletes documents
that already exist but are absent from ``PRICING_SERVICES`` below.

Run from the backend directory:

    python scripts/seed_pricing_services.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.firestore_client import get_firestore_client
from app.repositories.pricing_service_repository import PricingServiceRepository

PRICING_SERVICES: list[dict] = [
    {
        "service_id": "aws_lambda",
        "to_know": {
            "llm": [
                "requests_per_user_per_month",
                "average_execution_time_ms",
                "memory_mb",
            ],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Requests",
                "unit": "1000000_requests",
                "price_per_million": 0.2,
            },
            {
                "name": "Compute Duration",
                "unit": "gb_second",
                "price_per_gb_second": 0.0000166667,
            },
        ],
        "free_tier": {
            "requests": 1_000_000,
            "compute_gb_seconds": 400_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    requests_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_user_per_month\", 0)\n"
            "    )\n"
            "    average_execution_time_ms = max(\n"
            "        0,\n"
            "        inputs.get(\"average_execution_time_ms\", 0)\n"
            "    )\n"
            "    memory_mb = min(\n"
            "        10240,\n"
            "        max(128, inputs.get(\"memory_mb\", 128))\n"
            "    )\n"
            "\n"
            "    request_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Requests\"\n"
            "    )\n"
            "    compute_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Compute Duration\"\n"
            "    )\n"
            "\n"
            "    monthly_requests = users * requests_per_user_per_month\n"
            "\n"
            "    free_requests = free_tier.get(\"requests\", 0)\n"
            "    billable_requests = max(\n"
            "        0,\n"
            "        monthly_requests - free_requests\n"
            "    )\n"
            "\n"
            "    request_cost = (\n"
            "        billable_requests / 1_000_000\n"
            "    ) * request_sku[\"price_per_million\"]\n"
            "\n"
            "    memory_gb = memory_mb / 1024\n"
            "    execution_seconds = average_execution_time_ms / 1000\n"
            "\n"
            "    compute_gb_seconds = (\n"
            "        monthly_requests\n"
            "        * memory_gb\n"
            "        * execution_seconds\n"
            "    )\n"
            "\n"
            "    free_compute_gb_seconds = free_tier.get(\n"
            "        \"compute_gb_seconds\",\n"
            "        0\n"
            "    )\n"
            "    billable_compute_gb_seconds = max(\n"
            "        0,\n"
            "        compute_gb_seconds - free_compute_gb_seconds\n"
            "    )\n"
            "\n"
            "    compute_cost = (\n"
            "        billable_compute_gb_seconds\n"
            "        * compute_sku[\"price_per_gb_second\"]\n"
            "    )\n"
            "\n"
            "    estimated_price = request_cost + compute_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "gcp_cloud_storage",
        "to_know": {
            "llm": [
                "monthly_reads_per_file",
            ],
            "static": [
                "documents_per_month",
                "average_document_size_mb",
            ],
        },
        "skus": [
            {
                "name": "Storage",
                "unit": "gb_month",
                "price_per_gb": 0.022,
            },
            {
                "name": "Operations",
                "unit": "1000_operations",
                "price_per_1000": 0.005,
            },
            {
                "name": "Network Egress",
                "unit": "gb",
                "price_per_gb": 0.12,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    documents_per_month = max(0, inputs.get(\"documents_per_month\", 0))\n"
            "    average_document_size_mb = max(0, inputs.get(\"average_document_size_mb\", 0))\n"
            "    monthly_reads_per_file = max(0, inputs.get(\"monthly_reads_per_file\", 0))\n"
            "\n"
            "    storage_gb = (\n"
            "        documents_per_month * average_document_size_mb\n"
            "    ) / 1024\n"
            "\n"
            "    operations = (\n"
            "        documents_per_month\n"
            "        + (documents_per_month * monthly_reads_per_file)\n"
            "    )\n"
            "\n"
            "    network_egress_gb = (\n"
            "        documents_per_month\n"
            "        * monthly_reads_per_file\n"
            "        * average_document_size_mb\n"
            "    ) / 1024\n"
            "\n"
            "    storage_sku = next(s for s in skus if s[\"name\"] == \"Storage\")\n"
            "    operations_sku = next(s for s in skus if s[\"name\"] == \"Operations\")\n"
            "    network_sku = next(s for s in skus if s[\"name\"] == \"Network Egress\")\n"
            "\n"
            "    storage_cost = storage_gb * storage_sku[\"price_per_gb\"]\n"
            "    operations_cost = (operations / 1000) * operations_sku[\"price_per_1000\"]\n"
            "    network_cost = network_egress_gb * network_sku[\"price_per_gb\"]\n"
            "\n"
            "    estimated_price = storage_cost + operations_cost + network_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "aws_elasticache_memcached",
        "to_know": {
            "llm": [
                "memory_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "M1",
                "min_memory_gb": 1,
                "max_memory_gb": 4,
                "price_per_gb_hour": 0.049,
            },
            {
                "name": "M2",
                "min_memory_gb": 5,
                "max_memory_gb": 10,
                "price_per_gb_hour": 0.027,
            },
            {
                "name": "M3",
                "min_memory_gb": 11,
                "max_memory_gb": 35,
                "price_per_gb_hour": 0.023,
            },
            {
                "name": "M4",
                "min_memory_gb": 36,
                "max_memory_gb": 100,
                "price_per_gb_hour": 0.019,
            },
            {
                "name": "M5",
                "min_memory_gb": 101,
                "max_memory_gb": None,
                "price_per_gb_hour": 0.016,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    required_memory_gb = max(0, inputs.get(\"memory_gb\", 0))\n"
            "    running_hours_per_month = 730\n"
            "\n"
            "    selected_sku = next(\n"
            "        (\n"
            "            sku for sku in skus\n"
            "            if required_memory_gb >= sku[\"min_memory_gb\"]\n"
            "            and (\n"
            "                sku[\"max_memory_gb\"] is None\n"
            "                or required_memory_gb <= sku[\"max_memory_gb\"]\n"
            "            )\n"
            "        ),\n"
            "        None\n"
            "    )\n"
            "\n"
            "    if selected_sku is None:\n"
            "        selected_sku = skus[0]\n"
            "        required_memory_gb = max(\n"
            "            required_memory_gb,\n"
            "            selected_sku[\"min_memory_gb\"]\n"
            "        )\n"
            "\n"
            "    billable_memory_gb = max(\n"
            "        required_memory_gb,\n"
            "        selected_sku[\"min_memory_gb\"]\n"
            "    )\n"
            "\n"
            "    estimated_price = (\n"
            "        billable_memory_gb\n"
            "        * selected_sku[\"price_per_gb_hour\"]\n"
            "        * running_hours_per_month\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "gcp_cloud_run",
        "to_know": {
            "llm": [
                "vcpu",
                "memory_gb",
                "average_execution_time_ms",
            ],
            "static": [
                "requests_per_month",
            ],
        },
        "skus": [
            {
                "name": "CPU",
                "unit": "vcpu_second",
                "price_per_vcpu_second": 0.000024,
            },
            {
                "name": "Memory",
                "unit": "gib_second",
                "price_per_gib_second": 0.0000025,
            },
            {
                "name": "Requests",
                "unit": "1000000_requests",
                "price_per_million": 0.4,
            },
        ],
        "free_tier": {
            "vcpu_seconds": 180_000,
            "gib_seconds": 360_000,
            "requests": 2_000_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    requests_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_month\", 0)\n"
            "    )\n"
            "    vcpu = max(\n"
            "        0,\n"
            "        inputs.get(\"vcpu\", 0)\n"
            "    )\n"
            "    memory_gb = max(\n"
            "        0,\n"
            "        inputs.get(\"memory_gb\", 0)\n"
            "    )\n"
            "    average_execution_time_ms = max(\n"
            "        0,\n"
            "        inputs.get(\"average_execution_time_ms\", 0)\n"
            "    )\n"
            "\n"
            "    cpu_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"CPU\"\n"
            "    )\n"
            "    memory_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Memory\"\n"
            "    )\n"
            "    requests_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Requests\"\n"
            "    )\n"
            "\n"
            "    execution_seconds = average_execution_time_ms / 1000\n"
            "\n"
            "    total_vcpu_seconds = (\n"
            "        requests_per_month\n"
            "        * execution_seconds\n"
            "        * vcpu\n"
            "    )\n"
            "\n"
            "    total_gib_seconds = (\n"
            "        requests_per_month\n"
            "        * execution_seconds\n"
            "        * memory_gb\n"
            "    )\n"
            "\n"
            "    billable_vcpu_seconds = max(\n"
            "        0,\n"
            "        total_vcpu_seconds\n"
            "        - free_tier.get(\"vcpu_seconds\", 0)\n"
            "    )\n"
            "\n"
            "    billable_gib_seconds = max(\n"
            "        0,\n"
            "        total_gib_seconds\n"
            "        - free_tier.get(\"gib_seconds\", 0)\n"
            "    )\n"
            "\n"
            "    billable_requests = max(\n"
            "        0,\n"
            "        requests_per_month\n"
            "        - free_tier.get(\"requests\", 0)\n"
            "    )\n"
            "\n"
            "    cpu_cost = (\n"
            "        billable_vcpu_seconds\n"
            "        * cpu_sku[\"price_per_vcpu_second\"]\n"
            "    )\n"
            "\n"
            "    memory_cost = (\n"
            "        billable_gib_seconds\n"
            "        * memory_sku[\"price_per_gib_second\"]\n"
            "    )\n"
            "\n"
            "    request_cost = (\n"
            "        billable_requests / 1_000_000\n"
            "    ) * requests_sku[\"price_per_million\"]\n"
            "\n"
            "    estimated_price = (\n"
            "        cpu_cost\n"
            "        + memory_cost\n"
            "        + request_cost\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "gcp_cloud_functions",
        "to_know": {
            "llm": [
                "requests_per_user_per_month",
                "average_execution_time_ms",
                "memory_mb",
                "cpu",
            ],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Requests",
                "unit": "1000000_requests",
                "price_per_million": 0.4,
            },
            {
                "name": "CPU",
                "unit": "vcpu_second",
                "price_per_vcpu_second": 0.000024,
            },
            {
                "name": "Memory",
                "unit": "gib_second",
                "price_per_gib_second": 0.0000025,
            },
        ],
        "free_tier": {
            "requests": 2_000_000,
            "cpu_seconds": 180_000,
            "memory_gib_seconds": 360_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    requests_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_user_per_month\", 0)\n"
            "    )\n"
            "    average_execution_time_ms = max(\n"
            "        0,\n"
            "        inputs.get(\"average_execution_time_ms\", 0)\n"
            "    )\n"
            "    memory_mb = min(\n"
            "        32768,\n"
            "        max(128, inputs.get(\"memory_mb\", 256))\n"
            "    )\n"
            "    cpu = max(\n"
            "        0.08,\n"
            "        inputs.get(\"cpu\", 0.167)\n"
            "    )\n"
            "\n"
            "    request_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Requests\"\n"
            "    )\n"
            "    cpu_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"CPU\"\n"
            "    )\n"
            "    memory_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Memory\"\n"
            "    )\n"
            "\n"
            "    monthly_requests = users * requests_per_user_per_month\n"
            "\n"
            "    free_requests = free_tier.get(\"requests\", 0)\n"
            "    billable_requests = max(\n"
            "        0,\n"
            "        monthly_requests - free_requests\n"
            "    )\n"
            "\n"
            "    request_cost = (\n"
            "        billable_requests / 1_000_000\n"
            "    ) * request_sku[\"price_per_million\"]\n"
            "\n"
            "    execution_seconds = average_execution_time_ms / 1000\n"
            "    memory_gib = memory_mb / 1024\n"
            "\n"
            "    cpu_seconds = (\n"
            "        monthly_requests\n"
            "        * execution_seconds\n"
            "        * cpu\n"
            "    )\n"
            "\n"
            "    memory_gib_seconds = (\n"
            "        monthly_requests\n"
            "        * execution_seconds\n"
            "        * memory_gib\n"
            "    )\n"
            "\n"
            "    free_cpu_seconds = free_tier.get(\n"
            "        \"cpu_seconds\",\n"
            "        0\n"
            "    )\n"
            "    billable_cpu_seconds = max(\n"
            "        0,\n"
            "        cpu_seconds - free_cpu_seconds\n"
            "    )\n"
            "\n"
            "    free_memory_gib_seconds = free_tier.get(\n"
            "        \"memory_gib_seconds\",\n"
            "        0\n"
            "    )\n"
            "    billable_memory_gib_seconds = max(\n"
            "        0,\n"
            "        memory_gib_seconds - free_memory_gib_seconds\n"
            "    )\n"
            "\n"
            "    cpu_cost = (\n"
            "        billable_cpu_seconds\n"
            "        * cpu_sku[\"price_per_vcpu_second\"]\n"
            "    )\n"
            "\n"
            "    memory_cost = (\n"
            "        billable_memory_gib_seconds\n"
            "        * memory_sku[\"price_per_gib_second\"]\n"
            "    )\n"
            "\n"
            "    estimated_price = (\n"
            "        request_cost\n"
            "        + cpu_cost\n"
            "        + memory_cost\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "gcp_cloud_monitoring",
        "to_know": {
            "llm": [
                "log_ingestion_gb_per_month",
                "log_storage_gb",
                "monitoring_metrics_mib_per_month",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Log Ingestion",
                "unit": "gib",
                "price_per_gib": 0.5,
            },
            {
                "name": "Extended Log Retention",
                "unit": "gib_month",
                "price_per_gib_month": 0.01,
            },
            {
                "name": "Monitoring Metrics Tier 1",
                "from_mib": 150,
                "to_mib": 100_000,
                "price_per_mib": 0.258,
            },
            {
                "name": "Monitoring Metrics Tier 2",
                "from_mib": 100_000,
                "to_mib": 250_000,
                "price_per_mib": 0.151,
            },
            {
                "name": "Monitoring Metrics Tier 3",
                "from_mib": 250_000,
                "to_mib": None,
                "price_per_mib": 0.061,
            },
        ],
        "free_tier": {
            "log_ingestion_gib": 50,
            "log_retention_days": 30,
            "monitoring_metrics_mib": 150,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    log_ingestion_gib = max(\n"
            "        0,\n"
            "        inputs.get(\"log_ingestion_gb_per_month\", 0)\n"
            "    )\n"
            "    extended_log_storage_gib = max(\n"
            "        0,\n"
            "        inputs.get(\"log_storage_gb\", 0)\n"
            "    )\n"
            "    monitoring_metrics_mib = max(\n"
            "        0,\n"
            "        inputs.get(\"monitoring_metrics_mib_per_month\", 0)\n"
            "    )\n"
            "\n"
            "    log_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Log Ingestion\"\n"
            "    )\n"
            "    retention_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Extended Log Retention\"\n"
            "    )\n"
            "\n"
            "    billable_logs = max(\n"
            "        0,\n"
            "        log_ingestion_gib - free_tier.get(\"log_ingestion_gib\", 0)\n"
            "    )\n"
            "    log_cost = billable_logs * log_sku[\"price_per_gib\"]\n"
            "\n"
            "    retention_cost = (\n"
            "        extended_log_storage_gib\n"
            "        * retention_sku[\"price_per_gib_month\"]\n"
            "    )\n"
            "\n"
            "    remaining_metrics = max(\n"
            "        0,\n"
            "        monitoring_metrics_mib\n"
            "        - free_tier.get(\"monitoring_metrics_mib\", 0)\n"
            "    )\n"
            "    metrics_cost = 0\n"
            "\n"
            "    metric_tiers = sorted(\n"
            "        [sku for sku in skus if \"price_per_mib\" in sku],\n"
            "        key=lambda sku: sku[\"from_mib\"]\n"
            "    )\n"
            "\n"
            "    for tier in metric_tiers:\n"
            "        if remaining_metrics <= 0:\n"
            "            break\n"
            "\n"
            "        tier_start = tier[\"from_mib\"]\n"
            "        tier_end = tier[\"to_mib\"]\n"
            "\n"
            "        if tier_end is None:\n"
            "            tier_capacity = remaining_metrics\n"
            "        else:\n"
            "            tier_capacity = tier_end - tier_start\n"
            "\n"
            "        tier_usage = min(remaining_metrics, tier_capacity)\n"
            "        metrics_cost += tier_usage * tier[\"price_per_mib\"]\n"
            "        remaining_metrics -= tier_usage\n"
            "\n"
            "    total = log_cost + retention_cost + metrics_cost\n"
            "\n"
            "    return round(total, 2)"
        ),
        "calculation_tag": "tiered",
    },
    {
        "service_id": "gcp_api_gateway",
        "to_know": {
            "llm": [],
            "static": [
                "requests_per_month",
            ],
        },
        "skus": [
            {
                "name": "API Calls Tier 1",
                "from_requests": 2_000_000,
                "up_to_requests": 1_000_000_000,
                "unit": "1000000_requests",
                "price_per_million": 3.0,
            },
            {
                "name": "API Calls Tier 2",
                "from_requests": 1_000_000_000,
                "up_to_requests": None,
                "unit": "1000000_requests",
                "price_per_million": 1.5,
            },
        ],
        "free_tier": {
            "requests_per_month": 2_000_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    requests_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_month\", 0)\n"
            "    )\n"
            "\n"
            "    free_requests = free_tier.get(\n"
            "        \"requests_per_month\",\n"
            "        0\n"
            "    )\n"
            "\n"
            "    if requests_per_month <= free_requests:\n"
            "        return 0.0\n"
            "\n"
            "    estimated_price = 0.0\n"
            "\n"
            "    for sku in skus:\n"
            "        tier_start = sku[\"from_requests\"]\n"
            "        tier_end = sku[\"up_to_requests\"]\n"
            "\n"
            "        if requests_per_month <= tier_start:\n"
            "            continue\n"
            "\n"
            "        if tier_end is None:\n"
            "            requests_in_tier = (\n"
            "                requests_per_month - tier_start\n"
            "            )\n"
            "        else:\n"
            "            requests_in_tier = (\n"
            "                min(requests_per_month, tier_end)\n"
            "                - tier_start\n"
            "            )\n"
            "\n"
            "        requests_in_tier = max(0, requests_in_tier)\n"
            "\n"
            "        estimated_price += (\n"
            "            requests_in_tier / 1_000_000\n"
            "        ) * sku[\"price_per_million\"]\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "gcp_firestore",
        "to_know": {
            "llm": [
                "reads_per_day",
                "writes_per_day",
                "deletes_per_day",
                "database_storage_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Document Reads",
                "unit": "read",
                "price_per_unit": 0.0000006,
            },
            {
                "name": "Document Writes",
                "unit": "write",
                "price_per_unit": 0.0000018,
            },
            {
                "name": "Document Deletes",
                "unit": "delete",
                "price_per_unit": 0.0000002,
            },
            {
                "name": "Storage",
                "unit": "gb_month",
                "price_per_unit": 0.18,
            },
        ],
        "free_tier": {
            "database_storage_gb": 1,
            "reads_per_day": 50_000,
            "writes_per_day": 20_000,
            "deletes_per_day": 20_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    reads_per_day = max(0, inputs.get(\"reads_per_day\", 0))\n"
            "    writes_per_day = max(0, inputs.get(\"writes_per_day\", 0))\n"
            "    deletes_per_day = max(0, inputs.get(\"deletes_per_day\", 0))\n"
            "    database_storage_gb = max(0, inputs.get(\"database_storage_gb\", 0))\n"
            "\n"
            "    read_sku = next(s for s in skus if s[\"name\"] == \"Document Reads\")\n"
            "    write_sku = next(s for s in skus if s[\"name\"] == \"Document Writes\")\n"
            "    delete_sku = next(s for s in skus if s[\"name\"] == \"Document Deletes\")\n"
            "    storage_sku = next(s for s in skus if s[\"name\"] == \"Storage\")\n"
            "\n"
            "    billable_reads = max(\n"
            "        0,\n"
            "        (reads_per_day - free_tier.get(\"reads_per_day\", 0)) * 30\n"
            "    )\n"
            "    billable_writes = max(\n"
            "        0,\n"
            "        (writes_per_day - free_tier.get(\"writes_per_day\", 0)) * 30\n"
            "    )\n"
            "    billable_deletes = max(\n"
            "        0,\n"
            "        (deletes_per_day - free_tier.get(\"deletes_per_day\", 0)) * 30\n"
            "    )\n"
            "    billable_storage = max(\n"
            "        0,\n"
            "        database_storage_gb - free_tier.get(\"database_storage_gb\", 0)\n"
            "    )\n"
            "\n"
            "    reads_cost = billable_reads * read_sku[\"price_per_unit\"]\n"
            "    writes_cost = billable_writes * write_sku[\"price_per_unit\"]\n"
            "    deletes_cost = billable_deletes * delete_sku[\"price_per_unit\"]\n"
            "    storage_cost = billable_storage * storage_sku[\"price_per_unit\"]\n"
            "\n"
            "    total = reads_cost + writes_cost + deletes_cost + storage_cost\n"
            "\n"
            "    return round(total, 2)"
        ),
    },
    {
        "service_id": "gcp_firebase_auth",
        "to_know": {
            "llm": [],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Tier 1 MAU (50,001 - 100,000)",
                "from": 50_000,
                "to": 100_000,
                "price_per_mau": 0.0055,
            },
            {
                "name": "Tier 1 MAU (100,001 - 1,000,000)",
                "from": 100_000,
                "to": 1_000_000,
                "price_per_mau": 0.0046,
            },
            {
                "name": "Tier 1 MAU (1,000,001 - 10,000,000)",
                "from": 1_000_000,
                "to": 10_000_000,
                "price_per_mau": 0.0032,
            },
            {
                "name": "Tier 1 MAU (10,000,000+)",
                "from": 10_000_000,
                "to": None,
                "price_per_mau": 0.0025,
            },
        ],
        "free_tier": {
            "monthly_active_users": 50_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "\n"
            "    free = free_tier.get(\"monthly_active_users\", 0)\n"
            "    billable = max(0, users - free)\n"
            "\n"
            "    total = 0\n"
            "    remaining = billable\n"
            "\n"
            "    for sku in skus:\n"
            "        start = sku[\"from\"]\n"
            "        end = sku[\"to\"]\n"
            "\n"
            "        if remaining <= 0:\n"
            "            break\n"
            "\n"
            "        if end is None:\n"
            "            tier_size = remaining\n"
            "        else:\n"
            "            tier_size = min(remaining, end - start)\n"
            "\n"
            "        total += tier_size * sku[\"price_per_mau\"]\n"
            "        remaining -= tier_size\n"
            "\n"
            "    return round(total, 2)"
        ),
        "calculation_tag": "tiered",
    },
    {
        "service_id": "gcp_firebase_messaging",
        "to_know": {
            "llm": [],
            "static": [],
        },
        "skus": [
            {
                "name": "Firebase Cloud Messaging",
                "unit": "messages",
                "price_per_unit": 0,
            },
        ],
        "free_tier": {
            "messages": "unlimited",
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    return 0.0"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "gcp_cloud_sql",
        "to_know": {
            "llm": [
                "cpu",
                "ram_gb",
                "database_storage_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Sandbox",
                "cpu": 2,
                "ram_gb": 8,
                "database_storage_gb": 10,
                "monthly_price": 140,
                "monthly_price_min": 130,
                "monthly_price_max": 150,
            },
            {
                "name": "Development",
                "cpu": 4,
                "ram_gb": 32,
                "database_storage_gb": 250,
                "monthly_price": 600,
                "monthly_price_min": 550,
                "monthly_price_max": 650,
            },
            {
                "name": "Production",
                "cpu": 8,
                "ram_gb": 64,
                "database_storage_gb": 250,
                "monthly_price": 1400,
                "monthly_price_min": 1300,
                "monthly_price_max": 1500,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    required_cpu = max(0, inputs.get(\"cpu\", 0))\n"
            "    required_ram_gb = max(0, inputs.get(\"ram_gb\", 0))\n"
            "    required_database_storage_gb = max(0, inputs.get(\"database_storage_gb\", 0))\n"
            "\n"
            "    matching_skus = [\n"
            "        sku for sku in skus\n"
            "        if sku[\"cpu\"] >= required_cpu\n"
            "        and sku[\"ram_gb\"] >= required_ram_gb\n"
            "        and sku[\"database_storage_gb\"] >= required_database_storage_gb\n"
            "    ]\n"
            "\n"
            "    if not matching_skus:\n"
            "        raise ValueError(\n"
            "            \"No Cloud SQL package supports the requested CPU, RAM, and database storage requirements.\"\n"
            "        )\n"
            "\n"
            "    selected_sku = min(\n"
            "        matching_skus,\n"
            "        key=lambda sku: (\n"
            "            sku[\"monthly_price\"],\n"
            "            sku[\"cpu\"],\n"
            "            sku[\"ram_gb\"],\n"
            "            sku[\"database_storage_gb\"]\n"
            "        )\n"
            "    )\n"
            "\n"
            "    return round(selected_sku[\"monthly_price\"], 2)"
        ),
    },
    {
        "service_id": "aws_s3",
        "to_know": {
            "llm": {
                "prompt": (
                    "Based on the product description and requirements, estimate the "
                    "average number of times each stored document will be downloaded "
                    "or read per month. Return JSON only in this format: "
                    '{\"monthly_reads_per_file\": number}. Use a realistic conservative '
                    "estimate."
                ),
            },
            "static": [
                "documents_per_month",
                "average_document_size_mb",
            ],
        },
        "skus": [
            {
                "name": "Storage",
                "description": "S3 Standard storage",
                "unit": "GB-month",
                "price_per_gb": 0.023,
            },
            {
                "name": "Write Requests",
                "description": "PUT, COPY, POST and LIST requests",
                "unit": "1000 requests",
                "price_per_1000": 0.005,
            },
            {
                "name": "Read Requests",
                "description": "GET requests",
                "unit": "1000 requests",
                "price_per_1000": 0.0004,
            },
            {
                "name": "Data Transfer Out",
                "description": "Data downloaded from S3 to the internet",
                "unit": "GB",
                "price_per_gb": 0.09,
            },
        ],
        "free_tier": {
            "data_transfer_out_gb": 100,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    documents_per_month = max(0, inputs.get(\"documents_per_month\", 0))\n"
            "    average_document_size_mb = max(0, inputs.get(\"average_document_size_mb\", 0))\n"
            "    monthly_reads_per_file = max(0, inputs.get(\"monthly_reads_per_file\", 0))\n"
            "\n"
            "    storage_sku = next(sku for sku in skus if sku[\"name\"] == \"Storage\")\n"
            "    write_sku = next(sku for sku in skus if sku[\"name\"] == \"Write Requests\")\n"
            "    read_sku = next(sku for sku in skus if sku[\"name\"] == \"Read Requests\")\n"
            "    transfer_sku = next(sku for sku in skus if sku[\"name\"] == \"Data Transfer Out\")\n"
            "\n"
            "    storage_gb = (documents_per_month * average_document_size_mb) / 1024\n"
            "    write_requests = documents_per_month\n"
            "    read_requests = documents_per_month * monthly_reads_per_file\n"
            "\n"
            "    data_transfer_out_gb = (\n"
            "        read_requests * average_document_size_mb\n"
            "    ) / 1024\n"
            "\n"
            "    free_transfer_gb = free_tier.get(\"data_transfer_out_gb\", 0)\n"
            "    billable_transfer_gb = max(\n"
            "        0,\n"
            "        data_transfer_out_gb - free_transfer_gb\n"
            "    )\n"
            "\n"
            "    storage_cost = storage_gb * storage_sku[\"price_per_gb\"]\n"
            "    write_cost = (\n"
            "        write_requests / 1000\n"
            "    ) * write_sku[\"price_per_1000\"]\n"
            "    read_cost = (\n"
            "        read_requests / 1000\n"
            "    ) * read_sku[\"price_per_1000\"]\n"
            "    transfer_cost = (\n"
            "        billable_transfer_gb * transfer_sku[\"price_per_gb\"]\n"
            "    )\n"
            "\n"
            "    estimated_price = (\n"
            "        storage_cost\n"
            "        + write_cost\n"
            "        + read_cost\n"
            "        + transfer_cost\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "aws_ec2",
        "to_know": {
            "llm": [
                "workload_type",
                "vcpu",
                "memory_gb",
                "running_hours_per_month",
            ],
            "static": [],
        },
        "skus": [
            {
                "group": "Burstable",
                "instances": [
                    {
                        "name": "t4g.nano",
                        "vcpu": 2,
                        "memory_gb": 0.5,
                        "price_per_hour": 0.0042,
                    },
                    {
                        "name": "t4g.micro",
                        "vcpu": 2,
                        "memory_gb": 1,
                        "price_per_hour": 0.0084,
                    },
                    {
                        "name": "t3.micro",
                        "vcpu": 2,
                        "memory_gb": 1,
                        "price_per_hour": 0.0104,
                    },
                    {
                        "name": "t3.small",
                        "vcpu": 2,
                        "memory_gb": 2,
                        "price_per_hour": 0.0208,
                    },
                    {
                        "name": "t3.medium",
                        "vcpu": 2,
                        "memory_gb": 4,
                        "price_per_hour": 0.0416,
                    },
                    {
                        "name": "t3.large",
                        "vcpu": 2,
                        "memory_gb": 8,
                        "price_per_hour": 0.0832,
                    },
                ],
            },
            {
                "group": "General Purpose",
                "instances": [
                    {
                        "name": "m7i.large",
                        "vcpu": 2,
                        "memory_gb": 8,
                        "price_per_hour": 0.1,
                    },
                ],
            },
            {
                "group": "Compute Optimized",
                "instances": [
                    {
                        "name": "c7i.large",
                        "vcpu": 2,
                        "memory_gb": 4,
                        "price_per_hour": 0.09,
                    },
                ],
            },
            {
                "group": "Memory Optimized",
                "instances": [
                    {
                        "name": "r7i.large",
                        "vcpu": 2,
                        "memory_gb": 16,
                        "price_per_hour": 0.13,
                    },
                ],
            },
            {
                "group": "GPU",
                "instances": [
                    {
                        "name": "g4dn.xlarge",
                        "vcpu": 4,
                        "memory_gb": 16,
                        "price_per_hour": 0.53,
                    },
                ],
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    workload_type = inputs.get(\"workload_type\", \"Burstable\")\n"
            "    required_vcpu = max(0, inputs.get(\"vcpu\", 0))\n"
            "    required_memory_gb = max(0, inputs.get(\"memory_gb\", 0))\n"
            "    running_hours_per_month = min(\n"
            "        730,\n"
            "        max(0, inputs.get(\"running_hours_per_month\", 0))\n"
            "    )\n"
            "\n"
            "    selected_group = next(\n"
            "        (\n"
            "            group for group in skus\n"
            "            if group[\"group\"] == workload_type\n"
            "        ),\n"
            "        None\n"
            "    )\n"
            "\n"
            "    if selected_group is None:\n"
            "        selected_group = next(\n"
            "            group for group in skus\n"
            "            if group[\"group\"] == \"Burstable\"\n"
            "        )\n"
            "\n"
            "    matching_instances = [\n"
            "        instance\n"
            "        for instance in selected_group[\"instances\"]\n"
            "        if instance[\"vcpu\"] >= required_vcpu\n"
            "        and instance[\"memory_gb\"] >= required_memory_gb\n"
            "    ]\n"
            "\n"
            "    if matching_instances:\n"
            "        selected_instance = min(\n"
            "            matching_instances,\n"
            "            key=lambda instance: (\n"
            "                instance[\"price_per_hour\"],\n"
            "                instance[\"vcpu\"],\n"
            "                instance[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "    else:\n"
            "        selected_instance = max(\n"
            "            selected_group[\"instances\"],\n"
            "            key=lambda instance: (\n"
            "                instance[\"vcpu\"],\n"
            "                instance[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "\n"
            "    estimated_price = (\n"
            "        running_hours_per_month\n"
            "        * selected_instance[\"price_per_hour\"]\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "aws_api_gateway",
        "to_know": {
            "llm": [
                "api_type",
            ],
            "static": [
                "requests_per_month",
                "messages_per_month",
                "connection_minutes_per_month",
            ],
        },
        "skus": [
            {
                "name": "HTTP API",
                "pricing_type": "tiered",
                "tiers": [
                    {
                        "from_requests": 0,
                        "up_to_requests": 300_000_000,
                        "price_per_million": 1.0,
                    },
                    {
                        "from_requests": 300_000_000,
                        "up_to_requests": None,
                        "price_per_million": 0.9,
                    },
                ],
            },
            {
                "name": "REST API",
                "pricing_type": "tiered",
                "tiers": [
                    {
                        "from_requests": 0,
                        "up_to_requests": 333_000_000,
                        "price_per_million": 3.5,
                    },
                    {
                        "from_requests": 333_000_000,
                        "up_to_requests": 1_000_000_000,
                        "price_per_million": 2.8,
                    },
                    {
                        "from_requests": 1_000_000_000,
                        "up_to_requests": 20_000_000_000,
                        "price_per_million": 2.38,
                    },
                    {
                        "from_requests": 20_000_000_000,
                        "up_to_requests": None,
                        "price_per_million": 1.51,
                    },
                ],
            },
            {
                "name": "WebSocket API",
                "pricing_type": "multi_metric",
                "message_price_per_million": 1.0,
                "connection_price_per_million_minutes": 0.25,
            },
        ],
        "free_tier": {
            "http_requests": 1_000_000,
            "rest_requests": 1_000_000,
            "websocket_messages": 1_000_000,
            "websocket_connection_minutes": 750_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    api_type = inputs.get(\"api_type\", \"HTTP API\")\n"
            "\n"
            "    selected_sku = next(\n"
            "        (\n"
            "            sku for sku in skus\n"
            "            if sku[\"name\"] == api_type\n"
            "        ),\n"
            "        next(sku for sku in skus if sku[\"name\"] == \"HTTP API\")\n"
            "    )\n"
            "\n"
            "    if selected_sku[\"name\"] == \"WebSocket API\":\n"
            "        messages_per_month = max(\n"
            "            0,\n"
            "            inputs.get(\"messages_per_month\", 0)\n"
            "        )\n"
            "        connection_minutes_per_month = max(\n"
            "            0,\n"
            "            inputs.get(\"connection_minutes_per_month\", 0)\n"
            "        )\n"
            "\n"
            "        billable_messages = max(\n"
            "            0,\n"
            "            messages_per_month\n"
            "            - free_tier.get(\"websocket_messages\", 0)\n"
            "        )\n"
            "        billable_connection_minutes = max(\n"
            "            0,\n"
            "            connection_minutes_per_month\n"
            "            - free_tier.get(\"websocket_connection_minutes\", 0)\n"
            "        )\n"
            "\n"
            "        message_cost = (\n"
            "            billable_messages / 1_000_000\n"
            "        ) * selected_sku[\"message_price_per_million\"]\n"
            "\n"
            "        connection_cost = (\n"
            "            billable_connection_minutes / 1_000_000\n"
            "        ) * selected_sku[\"connection_price_per_million_minutes\"]\n"
            "\n"
            "        estimated_price = message_cost + connection_cost\n"
            "        return round(estimated_price, 2)\n"
            "\n"
            "    requests_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_month\", 0)\n"
            "    )\n"
            "\n"
            "    free_tier_key = (\n"
            "        \"http_requests\"\n"
            "        if selected_sku[\"name\"] == \"HTTP API\"\n"
            "        else \"rest_requests\"\n"
            "    )\n"
            "\n"
            "    billable_requests = max(\n"
            "        0,\n"
            "        requests_per_month - free_tier.get(free_tier_key, 0)\n"
            "    )\n"
            "\n"
            "    remaining_requests = billable_requests\n"
            "    estimated_price = 0.0\n"
            "\n"
            "    for tier in selected_sku[\"tiers\"]:\n"
            "        tier_start = tier[\"from_requests\"]\n"
            "        tier_end = tier[\"up_to_requests\"]\n"
            "\n"
            "        if tier_end is None:\n"
            "            requests_in_tier = remaining_requests\n"
            "        else:\n"
            "            tier_capacity = tier_end - tier_start\n"
            "            requests_in_tier = min(\n"
            "                remaining_requests,\n"
            "                tier_capacity\n"
            "            )\n"
            "\n"
            "        estimated_price += (\n"
            "            requests_in_tier / 1_000_000\n"
            "        ) * tier[\"price_per_million\"]\n"
            "\n"
            "        remaining_requests -= requests_in_tier\n"
            "\n"
            "        if remaining_requests <= 0:\n"
            "            break\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "aws_cloudwatch",
        "to_know": {
            "llm": [
                "custom_metrics",
                "log_ingestion_gb_per_month",
                "log_storage_gb",
                "alarms",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Custom Metrics",
                "unit": "metric_month",
                "price_per_metric": 0.30,
            },
            {
                "name": "Log Ingestion",
                "unit": "gb",
                "price_per_gb": 0.50,
            },
            {
                "name": "Log Storage",
                "unit": "gb_month",
                "price_per_gb": 0.03,
            },
            {
                "name": "Standard Alarm",
                "unit": "alarm_month",
                "price_per_alarm": 0.10,
            },
        ],
        "free_tier": {
            "custom_metrics": 10,
            "log_ingestion_gb": 5,
            "log_storage_gb": 5,
            "alarms": 10,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    custom_metrics = max(0, inputs.get(\"custom_metrics\", 0))\n"
            "    log_ingestion_gb = max(0, inputs.get(\"log_ingestion_gb_per_month\", 0))\n"
            "    log_storage_gb = max(0, inputs.get(\"log_storage_gb\", 0))\n"
            "    alarms = max(0, inputs.get(\"alarms\", 0))\n"
            "\n"
            "    metrics_sku = next(s for s in skus if s[\"name\"] == \"Custom Metrics\")\n"
            "    ingestion_sku = next(s for s in skus if s[\"name\"] == \"Log Ingestion\")\n"
            "    storage_sku = next(s for s in skus if s[\"name\"] == \"Log Storage\")\n"
            "    alarm_sku = next(s for s in skus if s[\"name\"] == \"Standard Alarm\")\n"
            "\n"
            "    billable_metrics = max(\n"
            "        0, custom_metrics - free_tier.get(\"custom_metrics\", 0)\n"
            "    )\n"
            "    billable_ingestion = max(\n"
            "        0, log_ingestion_gb - free_tier.get(\"log_ingestion_gb\", 0)\n"
            "    )\n"
            "    billable_storage = max(\n"
            "        0, log_storage_gb - free_tier.get(\"log_storage_gb\", 0)\n"
            "    )\n"
            "    billable_alarms = max(\n"
            "        0, alarms - free_tier.get(\"alarms\", 0)\n"
            "    )\n"
            "\n"
            "    metrics_cost = billable_metrics * metrics_sku[\"price_per_metric\"]\n"
            "    ingestion_cost = billable_ingestion * ingestion_sku[\"price_per_gb\"]\n"
            "    storage_cost = billable_storage * storage_sku[\"price_per_gb\"]\n"
            "    alarm_cost = billable_alarms * alarm_sku[\"price_per_alarm\"]\n"
            "\n"
            "    estimated_price = (\n"
            "        metrics_cost + ingestion_cost + storage_cost + alarm_cost\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "aws_cognito",
        "to_know": {
            "llm": [],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Monthly Active User",
                "unit": "monthly_active_user",
                "price_per_mau": 0.015,
            },
        ],
        "free_tier": {
            "monthly_active_users": 10_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "\n"
            "    mau_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Monthly Active User\"\n"
            "    )\n"
            "\n"
            "    free_mau = free_tier.get(\"monthly_active_users\", 0)\n"
            "    billable_mau = max(0, users - free_mau)\n"
            "\n"
            "    estimated_price = billable_mau * mau_sku[\"price_per_mau\"]\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "aws_sns",
        "to_know": {
            "llm": [
                "notifications_per_user_per_month",
            ],
            "static": [
                "users",
                "notification_channel_count",
            ],
        },
        "skus": [
            {
                "name": "Publish Requests",
                "unit": "1000000_requests",
                "price_per_million": 0.50,
            },
            {
                "name": "Mobile Push Deliveries",
                "unit": "1000000_notifications",
                "price_per_million": 0.50,
            },
        ],
        "free_tier": {
            "publish_requests": 1_000_000,
            "mobile_push_deliveries": 1_000_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    channel_count = max(0, inputs.get(\"notification_channel_count\", 0))\n"
            "    if channel_count == 0:\n"
            "        return 0.0\n"
            "\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    notifications_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"notifications_per_user_per_month\", 0),\n"
            "    )\n"
            "\n"
            "    notifications = users * notifications_per_user_per_month\n"
            "\n"
            "    publish_sku = next(\n"
            "        s for s in skus if s[\"name\"] == \"Publish Requests\"\n"
            "    )\n"
            "    delivery_sku = next(\n"
            "        s for s in skus if s[\"name\"] == \"Mobile Push Deliveries\"\n"
            "    )\n"
            "\n"
            "    billable_publish = max(\n"
            "        0,\n"
            "        notifications - free_tier.get(\"publish_requests\", 0),\n"
            "    )\n"
            "    billable_deliveries = max(\n"
            "        0,\n"
            "        notifications - free_tier.get(\"mobile_push_deliveries\", 0),\n"
            "    )\n"
            "\n"
            "    publish_cost = (\n"
            "        billable_publish / 1_000_000\n"
            "    ) * publish_sku[\"price_per_million\"]\n"
            "    delivery_cost = (\n"
            "        billable_deliveries / 1_000_000\n"
            "    ) * delivery_sku[\"price_per_million\"]\n"
            "\n"
            "    total = publish_cost + delivery_cost\n"
            "\n"
            "    return round(total, 2)"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "aws_ses",
        "to_know": {
            "llm": [
                "emails_per_user_per_month",
                "average_attachment_size_mb",
            ],
            "static": [
                "users",
                "ses_free_tier_active",
            ],
        },
        "skus": [
            {
                "name": "Outbound Emails",
                "unit": "1000_emails",
                "price_per_thousand": 0.1,
            },
            {
                "name": "Outbound Attachment Data",
                "unit": "gb",
                "price_per_gb": 0.12,
            },
        ],
        "free_tier": {
            "message_charges_per_month": 3000,
            "eligibility_months": 12,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    emails_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"emails_per_user_per_month\", 0)\n"
            "    )\n"
            "    average_attachment_size_mb = max(\n"
            "        0,\n"
            "        inputs.get(\"average_attachment_size_mb\", 0)\n"
            "    )\n"
            "    free_tier_active = bool(inputs.get(\"ses_free_tier_active\", False))\n"
            "\n"
            "    outbound_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Outbound Emails\"\n"
            "    )\n"
            "    attachment_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Outbound Attachment Data\"\n"
            "    )\n"
            "\n"
            "    emails_per_month = users * emails_per_user_per_month\n"
            "\n"
            "    free_messages = (\n"
            "        free_tier.get(\"message_charges_per_month\", 0)\n"
            "        if free_tier_active\n"
            "        else 0\n"
            "    )\n"
            "    billable_emails = max(0, emails_per_month - free_messages)\n"
            "\n"
            "    email_cost = (\n"
            "        billable_emails / 1000\n"
            "    ) * outbound_sku[\"price_per_thousand\"]\n"
            "\n"
            "    attachment_data_gb = (\n"
            "        emails_per_month\n"
            "        * average_attachment_size_mb\n"
            "        / 1024\n"
            "    )\n"
            "    attachment_cost = (\n"
            "        attachment_data_gb\n"
            "        * attachment_sku[\"price_per_gb\"]\n"
            "    )\n"
            "\n"
            "    estimated_price = email_cost + attachment_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "aws_sqs",
        "to_know": {
            "llm": [
                "queue_type",
            ],
            "static": [
                "requests_per_month",
            ],
        },
        "skus": [
            {
                "name": "Standard",
                "tiers": [
                    {
                        "from_requests": 0,
                        "up_to_requests": 100_000_000_000,
                        "price_per_million": 0.4,
                    },
                    {
                        "from_requests": 100_000_000_000,
                        "up_to_requests": 200_000_000_000,
                        "price_per_million": 0.3,
                    },
                    {
                        "from_requests": 200_000_000_000,
                        "up_to_requests": None,
                        "price_per_million": 0.24,
                    },
                ],
            },
            {
                "name": "FIFO",
                "price_per_million": 0.5,
            },
        ],
        "free_tier": {
            "requests_per_month": 1_000_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    queue_type = inputs.get(\"queue_type\", \"Standard\")\n"
            "    requests_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_month\", 0)\n"
            "    )\n"
            "\n"
            "    free_requests = free_tier.get(\"requests_per_month\", 0)\n"
            "    billable_requests = max(\n"
            "        0,\n"
            "        requests_per_month - free_requests\n"
            "    )\n"
            "\n"
            "    selected_sku = next(\n"
            "        (\n"
            "            sku for sku in skus\n"
            "            if sku[\"name\"] == queue_type\n"
            "        ),\n"
            "        next(sku for sku in skus if sku[\"name\"] == \"Standard\")\n"
            "    )\n"
            "\n"
            "    if selected_sku[\"name\"] == \"FIFO\":\n"
            "        estimated_price = (\n"
            "            billable_requests / 1_000_000\n"
            "        ) * selected_sku[\"price_per_million\"]\n"
            "\n"
            "        return round(estimated_price, 2)\n"
            "\n"
            "    remaining_requests = billable_requests\n"
            "    estimated_price = 0.0\n"
            "\n"
            "    for tier in selected_sku[\"tiers\"]:\n"
            "        tier_start = tier[\"from_requests\"]\n"
            "        tier_end = tier[\"up_to_requests\"]\n"
            "\n"
            "        if tier_end is None:\n"
            "            requests_in_tier = remaining_requests\n"
            "        else:\n"
            "            tier_capacity = tier_end - tier_start\n"
            "            requests_in_tier = min(\n"
            "                remaining_requests,\n"
            "                tier_capacity\n"
            "            )\n"
            "\n"
            "        estimated_price += (\n"
            "            requests_in_tier / 1_000_000\n"
            "        ) * tier[\"price_per_million\"]\n"
            "\n"
            "        remaining_requests -= requests_in_tier\n"
            "\n"
            "        if remaining_requests <= 0:\n"
            "            break\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "aws_dynamodb",
        "to_know": {
            "llm": [
                "reads_per_user_per_month",
                "writes_per_user_per_month",
                "database_storage_gb",
            ],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Read Requests",
                "price_per_million": 0.0625,
            },
            {
                "name": "Write Requests",
                "price_per_million": 0.625,
            },
            {
                "name": "Storage",
                "price_per_gb": 0.25,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    reads_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"reads_per_user_per_month\", 0)\n"
            "    )\n"
            "    writes_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"writes_per_user_per_month\", 0)\n"
            "    )\n"
            "    database_storage_gb = max(0, inputs.get(\"database_storage_gb\", 0))\n"
            "\n"
            "    monthly_reads = users * reads_per_user_per_month\n"
            "    monthly_writes = users * writes_per_user_per_month\n"
            "\n"
            "    read_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Read Requests\"\n"
            "    )\n"
            "    write_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Write Requests\"\n"
            "    )\n"
            "    storage_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Storage\"\n"
            "    )\n"
            "\n"
            "    read_cost = (\n"
            "        monthly_reads / 1_000_000\n"
            "    ) * read_sku[\"price_per_million\"]\n"
            "\n"
            "    write_cost = (\n"
            "        monthly_writes / 1_000_000\n"
            "    ) * write_sku[\"price_per_million\"]\n"
            "\n"
            "    storage_cost = database_storage_gb * storage_sku[\"price_per_gb\"]\n"
            "\n"
            "    estimated_price = read_cost + write_cost + storage_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "aws_rds",
        "to_know": {
            "llm": [
                "vcpu",
                "memory_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "group": "Burstable",
                "instances": [
                    {
                        "name": "db.t4g.micro",
                        "vcpu": 2,
                        "memory_gb": 1,
                        "price_per_hour": 0.016,
                    },
                    {
                        "name": "db.t4g.small",
                        "vcpu": 2,
                        "memory_gb": 2,
                        "price_per_hour": 0.032,
                    },
                    {
                        "name": "db.t4g.medium",
                        "vcpu": 2,
                        "memory_gb": 4,
                        "price_per_hour": 0.064,
                    },
                    {
                        "name": "db.t4g.large",
                        "vcpu": 2,
                        "memory_gb": 8,
                        "price_per_hour": 0.128,
                    },
                ],
            },
            {
                "group": "General Purpose",
                "instances": [
                    {
                        "name": "db.m7g.large",
                        "vcpu": 2,
                        "memory_gb": 8,
                        "price_per_hour": 0.18,
                    },
                    {
                        "name": "db.m7g.xlarge",
                        "vcpu": 4,
                        "memory_gb": 16,
                        "price_per_hour": 0.36,
                    },
                ],
            },
            {
                "group": "Memory Optimized",
                "instances": [
                    {
                        "name": "db.r7g.large",
                        "vcpu": 2,
                        "memory_gb": 16,
                        "price_per_hour": 0.24,
                    },
                    {
                        "name": "db.r7g.xlarge",
                        "vcpu": 4,
                        "memory_gb": 32,
                        "price_per_hour": 0.48,
                    },
                ],
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    required_vcpu = max(0, inputs.get(\"vcpu\", 0))\n"
            "    required_memory_gb = max(0, inputs.get(\"memory_gb\", 0))\n"
            "\n"
            "    running_hours_per_month = 730\n"
            "\n"
            "    all_instances = [\n"
            "        instance\n"
            "        for group in skus\n"
            "        for instance in group[\"instances\"]\n"
            "    ]\n"
            "\n"
            "    matching_instances = [\n"
            "        instance\n"
            "        for instance in all_instances\n"
            "        if instance[\"vcpu\"] >= required_vcpu\n"
            "        and instance[\"memory_gb\"] >= required_memory_gb\n"
            "    ]\n"
            "\n"
            "    if matching_instances:\n"
            "        selected_instance = min(\n"
            "            matching_instances,\n"
            "            key=lambda instance: (\n"
            "                instance[\"price_per_hour\"],\n"
            "                instance[\"vcpu\"],\n"
            "                instance[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "    else:\n"
            "        selected_instance = max(\n"
            "            all_instances,\n"
            "            key=lambda instance: (\n"
            "                instance[\"vcpu\"],\n"
            "                instance[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "\n"
            "    estimated_price = (\n"
            "        running_hours_per_month\n"
            "        * selected_instance[\"price_per_hour\"]\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
        "calculation_tag": "group",
    },
    {
        "service_id": "aws_elasticache_redis",
        "to_know": {
            "llm": [
                "memory_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "cache.t4g.small",
                "memory_gb": 1.37,
                "vcpu": 2,
                "price_per_hour": 0.026,
            },
            {
                "name": "cache.t4g.medium",
                "memory_gb": 3.09,
                "vcpu": 2,
                "price_per_hour": 0.054,
            },
            {
                "name": "cache.r7g.large",
                "memory_gb": 13.07,
                "vcpu": 2,
                "price_per_hour": 0.136,
            },
            {
                "name": "cache.r7g.xlarge",
                "memory_gb": 26.32,
                "vcpu": 4,
                "price_per_hour": 0.28,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    required_memory_gb = max(0, inputs.get(\"memory_gb\", 0))\n"
            "    running_hours_per_month = 730\n"
            "\n"
            "    matching_instances = [\n"
            "        sku for sku in skus\n"
            "        if sku[\"memory_gb\"] >= required_memory_gb\n"
            "    ]\n"
            "\n"
            "    if matching_instances:\n"
            "        selected_instance = min(\n"
            "            matching_instances,\n"
            "            key=lambda sku: (\n"
            "                sku[\"price_per_hour\"],\n"
            "                sku[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "    else:\n"
            "        selected_instance = max(\n"
            "            skus,\n"
            "            key=lambda sku: sku[\"memory_gb\"]\n"
            "        )\n"
            "\n"
            "    estimated_price = (\n"
            "        running_hours_per_month\n"
            "        * selected_instance[\"price_per_hour\"]\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_entra_id",
        "to_know": {
            "llm": [],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Monthly Active User",
                "unit": "monthly_active_user",
                "price_per_mau": 0.03,
            },
        ],
        "free_tier": {
            "monthly_active_users": 50_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "\n"
            "    mau_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Monthly Active User\"\n"
            "    )\n"
            "\n"
            "    free_mau = free_tier.get(\"monthly_active_users\", 0)\n"
            "    billable_mau = max(0, users - free_mau)\n"
            "\n"
            "    estimated_price = billable_mau * mau_sku[\"price_per_mau\"]\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "azure_blob_storage",
        "to_know": {
            "llm": [
                "monthly_reads_per_file",
            ],
            "static": [
                "documents_per_month",
                "average_document_size_mb",
                "retention_months",
            ],
        },
        "skus": [
            {
                "name": "Storage",
                "access_tier": "Hot",
                "unit": "GB-month",
                "price_per_gb": 0.02,
            },
            {
                "name": "Read Operations",
                "unit": "10000_operations",
                "price_per_10000": 0.004,
            },
            {
                "name": "Write Operations",
                "unit": "10000_operations",
                "price_per_10000": 0.055,
            },
            {
                "name": "List and Other Operations",
                "unit": "10000_operations",
                "price_per_10000": 0.055,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    documents_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"documents_per_month\", 0)\n"
            "    )\n"
            "    average_document_size_mb = max(\n"
            "        0,\n"
            "        inputs.get(\"average_document_size_mb\", 0)\n"
            "    )\n"
            "    retention_months = max(\n"
            "        1,\n"
            "        inputs.get(\"retention_months\", 1)\n"
            "    )\n"
            "    monthly_reads_per_file = max(\n"
            "        0,\n"
            "        inputs.get(\"monthly_reads_per_file\", 0)\n"
            "    )\n"
            "\n"
            "    storage_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Storage\"\n"
            "    )\n"
            "    read_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Read Operations\"\n"
            "    )\n"
            "    write_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Write Operations\"\n"
            "    )\n"
            "    other_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"List and Other Operations\"\n"
            "    )\n"
            "\n"
            "    stored_documents = documents_per_month * retention_months\n"
            "\n"
            "    storage_gb = (\n"
            "        stored_documents\n"
            "        * average_document_size_mb\n"
            "    ) / 1024\n"
            "\n"
            "    write_operations = documents_per_month\n"
            "    read_operations = (\n"
            "        stored_documents\n"
            "        * monthly_reads_per_file\n"
            "    )\n"
            "\n"
            "    other_operations = documents_per_month\n"
            "\n"
            "    storage_cost = (\n"
            "        storage_gb\n"
            "        * storage_sku[\"price_per_gb\"]\n"
            "    )\n"
            "    read_cost = (\n"
            "        read_operations / 10000\n"
            "    ) * read_sku[\"price_per_10000\"]\n"
            "    write_cost = (\n"
            "        write_operations / 10000\n"
            "    ) * write_sku[\"price_per_10000\"]\n"
            "    other_cost = (\n"
            "        other_operations / 10000\n"
            "    ) * other_sku[\"price_per_10000\"]\n"
            "\n"
            "    estimated_price = (\n"
            "        storage_cost\n"
            "        + read_cost\n"
            "        + write_cost\n"
            "        + other_cost\n"
            "    )\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_sql_database",
        "to_know": {
            "llm": [
                "vcpu",
                "memory_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "group": "Burstable",
                "instances": [
                    {
                        "name": "B1ms",
                        "vcpu": 1,
                        "memory_gb": 2,
                        "price_per_month": 13,
                    },
                ],
            },
            {
                "group": "General Purpose",
                "instances": [
                    {
                        "name": "D2s v5",
                        "vcpu": 2,
                        "memory_gb": 8,
                        "price_per_month": 50,
                    },
                ],
            },
            {
                "group": "Memory Optimized",
                "instances": [
                    {
                        "name": "E2s v5",
                        "vcpu": 2,
                        "memory_gb": 16,
                        "price_per_month": 90,
                    },
                ],
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    required_vcpu = max(0, inputs.get(\"vcpu\", 0))\n"
            "    required_memory_gb = max(0, inputs.get(\"memory_gb\", 0))\n"
            "\n"
            "    all_instances = [\n"
            "        instance\n"
            "        for group in skus\n"
            "        for instance in group[\"instances\"]\n"
            "    ]\n"
            "\n"
            "    matching_instances = [\n"
            "        instance\n"
            "        for instance in all_instances\n"
            "        if instance[\"vcpu\"] >= required_vcpu\n"
            "        and instance[\"memory_gb\"] >= required_memory_gb\n"
            "    ]\n"
            "\n"
            "    if matching_instances:\n"
            "        selected_instance = min(\n"
            "            matching_instances,\n"
            "            key=lambda instance: (\n"
            "                instance[\"price_per_month\"],\n"
            "                instance[\"vcpu\"],\n"
            "                instance[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "    else:\n"
            "        selected_instance = max(\n"
            "            all_instances,\n"
            "            key=lambda instance: (\n"
            "                instance[\"vcpu\"],\n"
            "                instance[\"memory_gb\"]\n"
            "            )\n"
            "        )\n"
            "\n"
            "    estimated_price = selected_instance[\"price_per_month\"]\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_cosmos_db",
        "to_know": {
            "llm": [
                "capacity_mode",
                "request_units_per_user_per_month",
                "required_ru_per_second",
                "database_storage_gb",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Serverless",
                "pricing_type": "usage_based",
                "price_per_million_ru": 0.25,
                "storage_price_per_gb_month": 0.25,
            },
            {
                "name": "Provisioned Throughput",
                "pricing_type": "provisioned",
                "throughput_unit_ru_per_second": 100,
                "price_per_100_ru_hour": 0.008,
                "storage_price_per_gb_month": 0.25,
            },
            {
                "name": "Autoscale",
                "pricing_type": "autoscale",
                "throughput_unit_ru_per_second": 100,
                "price_per_100_ru_hour": 0.012,
                "storage_price_per_gb_month": 0.25,
            },
        ],
        "free_tier": {
            "database_storage_gb": 25,
            "throughput_ru_per_second": 1000,
            "account_limit": 1,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    valid_modes = {\"Serverless\", \"Provisioned Throughput\", \"Autoscale\"}\n"
            "    capacity_mode = inputs.get(\"capacity_mode\")\n"
            "    if capacity_mode not in valid_modes:\n"
            "        raise ValueError(\n"
            "            f\"Invalid capacity_mode: {capacity_mode!r}. \"\n"
            "            \"Must be Serverless, Provisioned Throughput, or Autoscale.\"\n"
            "        )\n"
            "\n"
            "    database_storage_gb = max(0, inputs.get(\"database_storage_gb\", 0))\n"
            "\n"
            "    selected_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == capacity_mode\n"
            "    )\n"
            "\n"
            "    free_storage_gb = free_tier.get(\"database_storage_gb\", 0)\n"
            "    billable_storage_gb = max(\n"
            "        0,\n"
            "        database_storage_gb - free_storage_gb\n"
            "    )\n"
            "\n"
            "    storage_cost = (\n"
            "        billable_storage_gb\n"
            "        * selected_sku[\"storage_price_per_gb_month\"]\n"
            "    )\n"
            "\n"
            "    if selected_sku[\"name\"] == \"Serverless\":\n"
            "        request_units_per_month = inputs.get(\"request_units_per_month\")\n"
            "        if request_units_per_month is None or request_units_per_month <= 0:\n"
            "            raise ValueError(\n"
            "                \"request_units_per_month is required for Serverless capacity mode.\"\n"
            "            )\n"
            "        price_per_million_ru = selected_sku.get(\n"
            "            \"price_per_million_ru\"\n"
            "        )\n"
            "\n"
            "        if price_per_million_ru is None:\n"
            "            price_per_million_ru = 0.25\n"
            "\n"
            "        request_cost = (\n"
            "            request_units_per_month / 1_000_000\n"
            "        ) * price_per_million_ru\n"
            "\n"
            "        estimated_price = request_cost + storage_cost\n"
            "        return round(estimated_price, 2)\n"
            "\n"
            "    required_ru_per_second = inputs.get(\"required_ru_per_second\")\n"
            "    if required_ru_per_second is None or required_ru_per_second < 0:\n"
            "        raise ValueError(\n"
            "            \"required_ru_per_second is required for Provisioned Throughput \"\n"
            "            \"or Autoscale capacity mode.\"\n"
            "        )\n"
            "    required_ru_per_second = max(0, required_ru_per_second)\n"
            "\n"
            "    free_ru_per_second = free_tier.get(\n"
            "        \"throughput_ru_per_second\",\n"
            "        0\n"
            "    )\n"
            "    billable_ru_per_second = max(\n"
            "        0,\n"
            "        required_ru_per_second - free_ru_per_second\n"
            "    )\n"
            "\n"
            "    throughput_units = math.ceil(\n"
            "        billable_ru_per_second\n"
            "        / selected_sku[\"throughput_unit_ru_per_second\"]\n"
            "    )\n"
            "\n"
            "    running_hours_per_month = 730\n"
            "\n"
            "    throughput_cost = (\n"
            "        throughput_units\n"
            "        * selected_sku[\"price_per_100_ru_hour\"]\n"
            "        * running_hours_per_month\n"
            "    )\n"
            "\n"
            "    estimated_price = throughput_cost + storage_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_functions",
        "to_know": {
            "llm": [
                "executions_per_user_per_month",
                "average_execution_time_ms",
                "memory_mb",
            ],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Executions",
                "unit": "1000000_executions",
                "price_per_million": 0.40,
            },
            {
                "name": "Execution Time",
                "unit": "gb_second",
                "price_per_gb_second": 0.000026,
            },
        ],
        "free_tier": {
            "executions": 250_000,
            "gb_seconds": 100_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    executions_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"executions_per_user_per_month\", 0)\n"
            "    )\n"
            "    average_execution_time_ms = max(\n"
            "        0,\n"
            "        inputs.get(\"average_execution_time_ms\", 0)\n"
            "    )\n"
            "    memory_mb = min(\n"
            "        4096,\n"
            "        max(128, inputs.get(\"memory_mb\", 128))\n"
            "    )\n"
            "\n"
            "    executions_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Executions\"\n"
            "    )\n"
            "    compute_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Execution Time\"\n"
            "    )\n"
            "\n"
            "    monthly_executions = users * executions_per_user_per_month\n"
            "\n"
            "    billable_executions = max(\n"
            "        0,\n"
            "        monthly_executions - free_tier[\"executions\"]\n"
            "    )\n"
            "\n"
            "    execution_cost = (\n"
            "        billable_executions / 1000000\n"
            "    ) * executions_sku[\"price_per_million\"]\n"
            "\n"
            "    memory_gb = memory_mb / 1024\n"
            "    execution_seconds = average_execution_time_ms / 1000\n"
            "\n"
            "    total_gb_seconds = (\n"
            "        monthly_executions\n"
            "        * memory_gb\n"
            "        * execution_seconds\n"
            "    )\n"
            "\n"
            "    billable_gb_seconds = max(\n"
            "        0,\n"
            "        total_gb_seconds - free_tier[\"gb_seconds\"]\n"
            "    )\n"
            "\n"
            "    compute_cost = (\n"
            "        billable_gb_seconds\n"
            "        * compute_sku[\"price_per_gb_second\"]\n"
            "    )\n"
            "\n"
            "    estimated_price = execution_cost + compute_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_api_management",
        "to_know": {
            "llm": [
                "requests_per_user_per_month",
            ],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Consumption Operations",
                "unit": "1000000_operations",
                "price_per_million": 3.5,
            },
        ],
        "free_tier": {
            "operations_per_month": 1_000_000,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    requests_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"requests_per_user_per_month\", 0)\n"
            "    )\n"
            "\n"
            "    monthly_operations = (\n"
            "        users * requests_per_user_per_month\n"
            "    )\n"
            "\n"
            "    free_operations = free_tier.get(\n"
            "        \"operations_per_month\",\n"
            "        0\n"
            "    )\n"
            "\n"
            "    billable_operations = max(\n"
            "        0,\n"
            "        monthly_operations - free_operations\n"
            "    )\n"
            "\n"
            "    operation_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Consumption Operations\"\n"
            "    )\n"
            "\n"
            "    estimated_price = (\n"
            "        billable_operations / 1_000_000\n"
            "    ) * operation_sku[\"price_per_million\"]\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_monitor",
        "to_know": {
            "llm": [
                "log_ingestion_gb_per_month",
                "log_storage_gb",
                "monitoring_alerts",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Log Ingestion",
                "unit": "gb",
                "price_per_gb": 2.76,
            },
            {
                "name": "Log Retention",
                "unit": "gb_month",
                "price_per_gb": 0.13,
            },
            {
                "name": "Metric Alert",
                "unit": "alert_month",
                "price_per_alert": 0.10,
            },
        ],
        "free_tier": {
            "log_ingestion_gb": 5,
            "log_retention_days": 31,
        },
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    log_ingestion_gb = max(\n"
            "        0, inputs.get(\"log_ingestion_gb_per_month\", 0)\n"
            "    )\n"
            "    log_storage_gb = max(0, inputs.get(\"log_storage_gb\", 0))\n"
            "    monitoring_alerts = max(0, inputs.get(\"monitoring_alerts\", 0))\n"
            "\n"
            "    ingestion_sku = next(\n"
            "        s for s in skus if s[\"name\"] == \"Log Ingestion\"\n"
            "    )\n"
            "    retention_sku = next(\n"
            "        s for s in skus if s[\"name\"] == \"Log Retention\"\n"
            "    )\n"
            "    alert_sku = next(s for s in skus if s[\"name\"] == \"Metric Alert\")\n"
            "\n"
            "    billable_ingestion = max(\n"
            "        0, log_ingestion_gb - free_tier.get(\"log_ingestion_gb\", 0)\n"
            "    )\n"
            "\n"
            "    ingestion_cost = billable_ingestion * ingestion_sku[\"price_per_gb\"]\n"
            "    retention_cost = log_storage_gb * retention_sku[\"price_per_gb\"]\n"
            "    alert_cost = monitoring_alerts * alert_sku[\"price_per_alert\"]\n"
            "\n"
            "    estimated_price = ingestion_cost + retention_cost + alert_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
        "calculation_tag": "normal",
    },
    {
        "service_id": "azure_notification_hubs",
        "to_know": {
            "llm": [
                "notifications_per_user_per_month",
            ],
            "static": [
                "users",
            ],
        },
        "skus": [
            {
                "name": "Free",
                "monthly_base_price": 0,
                "included_pushes": 1_000_000,
                "max_active_devices": 500,
                "additional_price_per_million": None,
            },
            {
                "name": "Basic",
                "monthly_base_price": 10,
                "included_pushes": 10_000_000,
                "max_active_devices": 200_000,
                "additional_price_per_million": 1,
            },
            {
                "name": "Standard",
                "monthly_base_price": 200,
                "included_pushes": 10_000_000,
                "max_active_devices": 10_000_000,
                "additional_price_per_million": None,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    users = max(0, inputs.get(\"users\", 0))\n"
            "    notifications_per_user_per_month = max(\n"
            "        0,\n"
            "        inputs.get(\"notifications_per_user_per_month\", 0)\n"
            "    )\n"
            "\n"
            "    monthly_pushes = users * notifications_per_user_per_month\n"
            "\n"
            "    free_sku = next(sku for sku in skus if sku[\"name\"] == \"Free\")\n"
            "    basic_sku = next(sku for sku in skus if sku[\"name\"] == \"Basic\")\n"
            "    standard_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Standard\"\n"
            "    )\n"
            "\n"
            "    if (\n"
            "        users <= free_sku[\"max_active_devices\"]\n"
            "        and monthly_pushes <= free_sku[\"included_pushes\"]\n"
            "    ):\n"
            "        return 0.0\n"
            "\n"
            "    if users <= basic_sku[\"max_active_devices\"]:\n"
            "        additional_pushes = max(\n"
            "            0,\n"
            "            monthly_pushes - basic_sku[\"included_pushes\"]\n"
            "        )\n"
            "        additional_cost = (\n"
            "            additional_pushes / 1_000_000\n"
            "        ) * basic_sku[\"additional_price_per_million\"]\n"
            "\n"
            "        return round(\n"
            "            basic_sku[\"monthly_base_price\"] + additional_cost,\n"
            "            2\n"
            "        )\n"
            "\n"
            "    if users <= standard_sku[\"max_active_devices\"]:\n"
            "        return round(standard_sku[\"monthly_base_price\"], 2)\n"
            "\n"
            "    raise ValueError(\n"
            "        \"The estimated number of active devices exceeds the supported Standard tier limit.\"\n"
            "    )"
        ),
        "calculation_tag": "group",
    },
    {
        "service_id": "azure_queue_storage",
        "to_know": {
            "llm": [
                "messages_per_month",
                "average_message_size_kb",
                "reads_per_message",
            ],
            "static": [],
        },
        "skus": [
            {
                "name": "Storage",
                "unit": "gb_month",
                "price_per_gb": 0.045,
            },
            {
                "name": "Class 1 Operations",
                "unit": "10000_operations",
                "price_per_10000": 0.004,
            },
            {
                "name": "Class 2 Operations",
                "unit": "10000_operations",
                "price_per_10000": 0.0004,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    messages_per_month = max(0, inputs.get(\"messages_per_month\", 0))\n"
            "    average_message_size_kb = max(\n"
            "        0,\n"
            "        inputs.get(\"average_message_size_kb\", 0)\n"
            "    )\n"
            "    reads_per_message = max(0, inputs.get(\"reads_per_message\", 0))\n"
            "\n"
            "    storage_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Storage\"\n"
            "    )\n"
            "    class1_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Class 1 Operations\"\n"
            "    )\n"
            "    class2_sku = next(\n"
            "        sku for sku in skus if sku[\"name\"] == \"Class 2 Operations\"\n"
            "    )\n"
            "\n"
            "    storage_gb = (\n"
            "        messages_per_month * average_message_size_kb\n"
            "    ) / (1024 * 1024)\n"
            "\n"
            "    class1_operations = messages_per_month\n"
            "    class2_operations = messages_per_month * reads_per_message\n"
            "\n"
            "    storage_cost = storage_gb * storage_sku[\"price_per_gb\"]\n"
            "\n"
            "    class1_cost = (\n"
            "        class1_operations / 10000\n"
            "    ) * class1_sku[\"price_per_10000\"]\n"
            "\n"
            "    class2_cost = (\n"
            "        class2_operations / 10000\n"
            "    ) * class2_sku[\"price_per_10000\"]\n"
            "\n"
            "    estimated_price = storage_cost + class1_cost + class2_cost\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
    {
        "service_id": "azure_cache_for_redis",
        "to_know": {
            "llm": [],
            "static": [],
        },
        "skus": [
            {
                "name": "Basic",
                "unit": "instance_month",
                "price_per_month": 16,
            },
        ],
        "free_tier": {},
        "script_calculation": (
            "def calculate_price(inputs, skus, free_tier):\n"
            "    basic_sku = next(\n"
            "        sku for sku in skus\n"
            "        if sku[\"name\"] == \"Basic\"\n"
            "    )\n"
            "\n"
            "    estimated_price = basic_sku[\"price_per_month\"]\n"
            "\n"
            "    return round(estimated_price, 2)"
        ),
    },
]


def seed() -> int:
    """Upsert every pricing service and print a created/updated/failed summary."""

    repository = PricingServiceRepository(get_firestore_client())

    created = 0
    updated = 0
    failed = 0

    for document in PRICING_SERVICES:
        service_id = document.get("service_id")
        if not service_id:
            failed += 1
            print("Failed to upsert document: missing 'service_id' field")
            continue

        try:
            was_created = repository.upsert(
                service_id=service_id,
                document=document,
            )
        except Exception as error:  # noqa: BLE001 - report and continue seeding
            failed += 1
            print(f"Failed to upsert '{service_id}': {error}")
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
