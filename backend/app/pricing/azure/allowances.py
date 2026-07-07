"""SKU key mapping and free-tier pool definitions for Azure pricing."""

from __future__ import annotations

# Calculator sku_key -> allowance key in FreeTierAllowance.allowances
SKU_ALLOWANCE_KEYS: dict[str, dict[str, str]] = {
    "Azure Container Apps": {
        "requests": "requests",
        "vcpu_seconds": "vcpu_seconds",
        "memory_gb_seconds": "memory_gb_seconds",
    },
    "Azure Functions": {
        "executions": "executions",
        "execution_time_gb_seconds": "gb_seconds",
    },
    "Azure Blob Storage": {
        "storage_gb_month": "storage_gb_months",
        "write_operations": "write_operations",
        "read_operations": "read_operations",
    },
    "Azure Queue Storage": {
        "storage_gb_month": "storage_gb_months",
        "queue_operations": "queue_operations",
    },
    "Azure Service Bus": {
        "operations": "queue_operations",
    },
    "Azure Cosmos DB": {
        "request_units": "request_units",
        "storage_gb_month": "storage_gb_months",
    },
    "Azure App Center": {
        "build_minutes": "build_minutes",
    },
    "Notification Hubs": {
        "notifications": "notifications",
    },
    "Application Insights": {
        "ingestion_gb": "ingestion_gb",
    },
    "Log Analytics": {
        "ingestion_gb": "ingestion_gb",
    },
    "Azure Monitor": {
        "custom_metrics": "custom_metrics",
        "alert_rules": "alert_rules",
    },
    "Azure Key Vault": {
        "operations": "operations",
    },
    "Azure App Configuration": {
        "requests": "requests",
    },
}

# Components consuming the same subscription grant share one pool.
FREE_TIER_POOLS: dict[str, list[str]] = {
    "azure_storage_account_free": ["Azure Blob Storage", "Azure Queue Storage"],
    "azure_container_apps_consumption": ["Azure Container Apps"],
    "azure_functions_consumption": ["Azure Functions"],
    "azure_service_bus_standard": ["Azure Service Bus"],
    "azure_cosmos_db_free": ["Azure Cosmos DB"],
    "azure_observability_free": [
        "Application Insights",
        "Log Analytics",
        "Azure Monitor",
    ],
    "azure_platform_free": [
        "Azure App Center",
        "Notification Hubs",
        "Azure Key Vault",
        "Azure App Configuration",
    ],
}

# Monthly grant amounts per shared pool (subscription-level policy constants).
POOL_FREE_TIER_ALLOWANCES: dict[str, dict[str, float]] = {
    "azure_storage_account_free": {
        "storage_gb_months": 5,
        "write_operations": 20_000,
        "read_operations": 20_000,
        "queue_operations": 20_000,
    },
    "azure_container_apps_consumption": {
        "requests": 2_000_000,
        "vcpu_seconds": 180_000,
        "memory_gb_seconds": 360_000,
    },
    "azure_functions_consumption": {
        "executions": 1_000_000,
        "gb_seconds": 400_000,
    },
    "azure_service_bus_standard": {
        "queue_operations": 13_000_000,
    },
    "azure_cosmos_db_free": {
        "request_units": 2_592_000,
        "storage_gb_months": 25,
    },
    "azure_observability_free": {
        "ingestion_gb": 5,
        "custom_metrics": 10,
        "alert_rules": 10,
    },
    "azure_platform_free": {
        "build_minutes": 240,
        "notifications": 1_000_000,
        "operations": 10_000,
        "requests": 10_000,
    },
}

_SERVICE_TO_POOL: dict[str, str] = {
    service: pool_id
    for pool_id, services in FREE_TIER_POOLS.items()
    for service in services
}


def pool_id_for_service(service: str) -> str | None:
    """Return the shared free-tier pool id for a service, if any."""
    return _SERVICE_TO_POOL.get(service)


def allowance_key_for_sku(service: str, sku_key: str) -> str | None:
    """Map a calculator sku_key to the allowance dict key, if eligible for free tier."""
    service_map = SKU_ALLOWANCE_KEYS.get(service, {})
    return service_map.get(sku_key)
