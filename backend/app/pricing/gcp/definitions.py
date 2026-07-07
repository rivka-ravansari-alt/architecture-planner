"""GCP service pricing model definitions.

These models describe which usage inputs are needed to derive billable SKUs.
Unit prices come from the Firestore gcp_catalog — not from the LLM.
"""

from __future__ import annotations

from app.pricing.schemas import (
    CalculatedSkuDefinition,
    FreeTierAllowance,
    GcpServicePricingModel,
    InputDataType,
    PricingModelDetails,
    ResourceRules,
    UsageInputDefinition,
)

_GCP_CLOUD_RUN_FUNCTIONS = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Run Functions",
    component_types=["service", "worker"],
    catalog_service_name="Cloud Run Functions",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="executions_per_month",
                description="Function invocation count.",
                unit="executions/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="avg_execution_duration_ms",
                description="Average execution time per invocation.",
                unit="milliseconds",
                data_type=InputDataType.float,
                min_value=0,
                default_value=200,
            ),
            UsageInputDefinition(
                key="memory_mb",
                description="Memory configured for the function.",
                unit="MB",
                data_type=InputDataType.integer,
                min_value=128,
                max_value=32768,
                default_value=512,
            ),
            UsageInputDefinition(
                key="network_egress_gb",
                description="Outbound data transfer from function executions.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Billable invocation count.",
                unit="executions/month",
                input_keys=["executions_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from executions_per_month.",
            ),
            CalculatedSkuDefinition(
                key="gb_seconds",
                description="Execution resource consumption (memory * duration).",
                unit="GB-seconds/month",
                input_keys=[
                    "executions_per_month",
                    "avg_execution_duration_ms",
                    "memory_mb",
                ],
                catalog_sku_roles=["cpu", "memory"],
                derivation=(
                    "executions_per_month * (avg_execution_duration_ms / 1000) * (memory_mb / 1024)"
                ),
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["network_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from network_egress_gb.",
            ),
        ],
        resource_rules=ResourceRules(
            min_resources={"memory_mb": 128},
            max_resources={"memory_mb": 32768},
        ),
        default_values={
            "avg_execution_duration_ms": 200,
            "memory_mb": 512,
            "network_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "requests": 2_000_000,
                "gb_seconds": 400_000,
            },
            notes="GCP Free Tier: 2M invocations and 400K GB-seconds per month (simplified).",
        ),
        billing_unit="requests and GB-seconds",
        billing_granularity="per invocation; GB-seconds per block",
        notes=["HTTP and event-triggered functions share the same execution meters."],
        warnings=["Min instances and VPC egress add separate meters not covered here."],
    ),
)

_GCP_CLOUD_RUN = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Run",
    component_types=["service", "worker"],
    catalog_service_name="Cloud Run",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="requests_per_month",
                description="Total HTTP/API requests handled per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="avg_request_duration_seconds",
                description="Average active processing time per request.",
                unit="seconds",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0.25,
            ),
            UsageInputDefinition(
                key="cpu",
                description="vCPU cores allocated per instance.",
                unit="vCPU",
                data_type=InputDataType.float,
                min_value=0.08,
                max_value=8,
                default_value=1.0,
            ),
            UsageInputDefinition(
                key="memory_gb",
                description="Memory allocated per instance.",
                unit="GiB",
                data_type=InputDataType.float,
                min_value=0.125,
                max_value=32,
                default_value=1.0,
            ),
            UsageInputDefinition(
                key="network_egress_gb",
                description="Outbound data transfer from services.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="min_instances",
                description="Minimum number of running instances (0 enables scale-to-zero).",
                unit="instances",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="vcpu_hours",
                description="Billable vCPU-hours across active instance time.",
                unit="vCPU-hours/month",
                input_keys=[
                    "requests_per_month",
                    "avg_request_duration_seconds",
                    "cpu",
                    "min_instances",
                ],
                catalog_sku_roles=["cpu"],
                derivation=(
                    "max(requests * duration * cpu / 3600, min_instances * cpu * hours_per_month)"
                ),
            ),
            CalculatedSkuDefinition(
                key="memory_gb_hours",
                description="Billable GiB-hours for allocated memory while instances are active.",
                unit="GiB-hours/month",
                input_keys=[
                    "requests_per_month",
                    "avg_request_duration_seconds",
                    "memory_gb",
                    "min_instances",
                ],
                catalog_sku_roles=["memory"],
                derivation=(
                    "max(requests * duration * memory_gb / 3600, "
                    "min_instances * memory_gb * hours_per_month)"
                ),
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Billable HTTP requests beyond free tier.",
                unit="requests/month",
                input_keys=["requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound data transfer.",
                unit="GB/month",
                input_keys=["network_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from network_egress_gb.",
            ),
        ],
        resource_rules=ResourceRules(
            supports_scale_to_zero=True,
            min_replicas_default=0,
            max_replicas_default=10,
            min_resources={"cpu": 0.08, "memory_gb": 0.125, "min_instances": 0},
            max_resources={"cpu": 8, "memory_gb": 32},
        ),
        default_values={
            "avg_request_duration_seconds": 0.25,
            "cpu": 1.0,
            "memory_gb": 1.0,
            "network_egress_gb": 0,
            "min_instances": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={"requests": 2_000_000},
            notes="GCP Free Tier: 2M requests per month (simplified).",
        ),
        billing_unit="vCPU-hours, GiB-hours, and requests",
        billing_granularity="per hour of instance runtime; egress per GB",
        notes=["Cloud Run Jobs and GPU SKUs are not modeled in v1."],
        warnings=["Minimum instance count materially affects compute SKUs when scale-to-zero is disabled."],
    ),
)

_GCP_CLOUD_SQL = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud SQL",
    component_types=["database"],
    catalog_service_name="Cloud SQL",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="instance_tier",
                description="Cloud SQL instance tier (e.g. db-f1-micro, db-g1-small).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="db-f1-micro",
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Allocated database storage.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=10,
                max_value=65536,
                default_value=10,
            ),
            UsageInputDefinition(
                key="backup_storage_gb",
                description="Backup retention storage beyond included allowance.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="hours_per_month",
                description="Billable instance hours when the database is online.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="instance_hours",
                description="Database instance charged per instance-hour.",
                unit="instance-hours/month",
                input_keys=["hours_per_month", "instance_tier"],
                catalog_sku_roles=["cpu"],
                derivation="hours_per_month (flat instance-hour meter from catalog).",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Allocated data storage.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="backup_storage_gb_month",
                description="Backup retention storage beyond included quota.",
                unit="GB-months",
                input_keys=["backup_storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from backup_storage_gb.",
            ),
        ],
        resource_rules=ResourceRules(
            min_resources={"storage_gb": 10},
            max_resources={"storage_gb": 65536},
        ),
        default_values={
            "instance_tier": "db-f1-micro",
            "storage_gb": 10,
            "backup_storage_gb": 0,
            "hours_per_month": 730,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "instance_hours": 730,
                "storage_gb_month": 10,
            },
            notes="GCP Free Tier: shared-core instance hours and 10 GB storage (simplified).",
        ),
        billing_unit="instance-hours and GB-months",
        billing_granularity="compute per hour; storage per GB-month",
        notes=["AlloyDB and Cloud SQL Enterprise Plus use different meters not covered in v1."],
        warnings=["High availability doubles instance-hour charges."],
    ),
)

_GCP_CLOUD_FIRESTORE = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Firestore",
    component_types=["database"],
    catalog_service_name="Cloud Firestore",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="storage_gb",
                description="Average database storage during the month.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="read_requests_per_month",
                description="Document read operations per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="write_requests_per_month",
                description="Document write operations per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="delete_requests_per_month",
                description="Document delete operations per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Stored data capacity.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="read_requests",
                description="Document read operations.",
                unit="requests/month",
                input_keys=["read_requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from read_requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="write_requests",
                description="Document write operations.",
                unit="requests/month",
                input_keys=["write_requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from write_requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="delete_requests",
                description="Document delete operations.",
                unit="requests/month",
                input_keys=["delete_requests_per_month"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from delete_requests_per_month.",
            ),
        ],
        resource_rules=ResourceRules(min_resources={"storage_gb": 0}),
        default_values={
            "read_requests_per_month": 0,
            "write_requests_per_month": 0,
            "delete_requests_per_month": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "storage_gb_month": 1,
                "read_requests": 50_000,
                "write_requests": 20_000,
                "delete_requests": 20_000,
            },
            notes="GCP Free Tier: 1 GB storage and daily read/write/delete quotas (simplified monthly).",
        ),
        billing_unit="GB-months and document operations",
        billing_granularity="per 100K operations; storage per GB-month",
        notes=["Multi-region and PITR add separate meters not covered in v1."],
        warnings=["Index storage and backup exports add meters not included in this model."],
    ),
)

_GCP_CLOUD_STORAGE = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Storage",
    component_types=["object_storage"],
    catalog_service_name="Cloud Storage",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="storage_gb",
                description="Average stored data volume during the month.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
            ),
            UsageInputDefinition(
                key="storage_class",
                description="Cloud Storage class (Standard, Nearline, Coldline, Archive).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Standard",
            ),
            UsageInputDefinition(
                key="write_operations",
                description="Class A operations (insert, update, delete).",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="read_operations",
                description="Class B operations (get, list).",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer to internet or other regions.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Stored data capacity.",
                unit="GB-months",
                input_keys=["storage_gb", "storage_class"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="Combined read/write request count.",
                unit="operations/month",
                input_keys=["write_operations", "read_operations"],
                catalog_sku_roles=["requests"],
                derivation="write_operations + read_operations.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        resource_rules=ResourceRules(
            min_resources={"storage_gb": 0},
            max_resources={"storage_gb": 5_000_000},
        ),
        default_values={
            "storage_class": "Standard",
            "write_operations": 0,
            "read_operations": 0,
            "data_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "storage_gb_month": 5,
                "requests": 50_000,
            },
            notes="GCP Free Tier: 5 GB Standard storage and 50K Class A + 50K Class B ops (simplified).",
        ),
        billing_unit="GB-months and per-operation",
        billing_granularity="storage per GB-month; operations per 1,000",
        notes=["Autoclass and dual-region buckets add separate meters."],
        warnings=["Cross-region replication multiplies storage and transfer costs."],
    ),
)

_GCP_CLOUD_PUBSUB = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Pub/Sub",
    component_types=["queue", "notification"],
    catalog_service_name="Cloud Pub/Sub",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="message_operations",
                description="Publish, subscribe, and acknowledge operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer for message payloads.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Pub/Sub message operation count.",
                unit="operations/month",
                input_keys=["message_operations"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from message_operations.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 10_000_000},
            notes="GCP Free Tier: 10 GiB/month message delivery (simplified as 10M ops).",
        ),
        billing_unit="operations",
        billing_granularity="per million operations",
        warnings=["Ordering keys and schema validation add separate meters."],
    ),
)

_GCP_CLOUD_TASKS = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Tasks",
    component_types=["queue", "worker"],
    catalog_service_name="Cloud Tasks",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="queue_operations",
                description="Task enqueue, dispatch, and delete operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Average task payload storage during the month.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer for task payloads.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="requests",
                description="Cloud Tasks API operation count.",
                unit="operations/month",
                input_keys=["queue_operations"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from queue_operations.",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_month",
                description="Task payload storage.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"storage_gb": 0, "data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={"requests": 1_000_000},
            notes="GCP Free Tier: 1M operations per month (simplified).",
        ),
        billing_unit="operations and GB-months",
        billing_granularity="per million operations",
        warnings=["HTTP target retries and OIDC tokens are simplified."],
    ),
)

_GCP_CLOUD_MEMORYSTORE = GcpServicePricingModel(
    cloud="gcp",
    service="Cloud Memorystore for Redis",
    component_types=["cache"],
    catalog_service_name="Cloud Memorystore for Redis",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="node_tier",
                description="Redis instance tier/capacity.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="basic_m1",
            ),
            UsageInputDefinition(
                key="hours_per_month",
                description="Billable node hours while cache instance is online.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer from Redis nodes.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="instance_hours",
                description="Billable Redis instance hours.",
                unit="hours/month",
                input_keys=["hours_per_month", "node_tier"],
                catalog_sku_roles=["cpu"],
                derivation="Direct mapping from hours_per_month.",
            ),
            CalculatedSkuDefinition(
                key="egress_gb",
                description="Billable outbound transfer.",
                unit="GB/month",
                input_keys=["data_egress_gb"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_egress_gb.",
            ),
        ],
        default_values={"node_tier": "basic_m1", "hours_per_month": 730, "data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={},
            notes="Cloud Memorystore has no always-free tier.",
        ),
        billing_unit="node-hours",
        billing_granularity="per hour",
        warnings=["Read replicas and cluster mode multiply node-hour charges."],
    ),
)

from app.pricing.gcp.definitions_platform import PLATFORM_GCP_PRICING_MODELS
from app.pricing.gcp.definitions_extended import EXTENDED_GCP_PRICING_MODELS

GCP_PRICING_MODELS: tuple[GcpServicePricingModel, ...] = (
    _GCP_CLOUD_RUN_FUNCTIONS,
    _GCP_CLOUD_RUN,
    _GCP_CLOUD_SQL,
    _GCP_CLOUD_FIRESTORE,
    _GCP_CLOUD_STORAGE,
    _GCP_CLOUD_PUBSUB,
    _GCP_CLOUD_TASKS,
    _GCP_CLOUD_MEMORYSTORE,
    *PLATFORM_GCP_PRICING_MODELS,
    *EXTENDED_GCP_PRICING_MODELS,
)
