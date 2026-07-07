"""Azure service pricing model definitions.

These models describe which usage inputs are needed to derive billable SKUs.
Unit prices come from the Firestore azure_catalog — not from the LLM.
"""

from __future__ import annotations

from app.pricing.schemas import (
    AzureServicePricingModel,
    CalculatedSkuDefinition,
    FreeTierAllowance,
    InputDataType,
    PricingModelDetails,
    ResourceRules,
    UsageInputDefinition,
)

_AZURE_CONTAINER_APPS = AzureServicePricingModel(
    cloud="azure",
    service="Azure Container Apps",
    component_types=["service", "worker"],
    catalog_service_name="Azure Container Apps",
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
                description="Average active processing time per request while a replica is busy.",
                unit="seconds",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0.25,
            ),
            UsageInputDefinition(
                key="cpu",
                description="vCPU cores allocated per replica.",
                unit="vCPU",
                data_type=InputDataType.float,
                min_value=0.25,
                max_value=4,
                default_value=0.5,
            ),
            UsageInputDefinition(
                key="memory_gb",
                description="Memory allocated per replica.",
                unit="GiB",
                data_type=InputDataType.float,
                min_value=0.5,
                max_value=8,
                default_value=1.0,
            ),
            UsageInputDefinition(
                key="network_egress_gb",
                description="Outbound data transfer from the app to clients or other services.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="min_replicas",
                description="Minimum number of running replicas (0 enables scale-to-zero).",
                unit="replicas",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="max_replicas",
                description="Maximum number of replicas under autoscale.",
                unit="replicas",
                data_type=InputDataType.integer,
                min_value=1,
                default_value=10,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="vcpu_seconds",
                description="Billable vCPU-seconds across active replica time.",
                unit="vCPU-seconds/month",
                input_keys=[
                    "requests_per_month",
                    "avg_request_duration_seconds",
                    "cpu",
                    "min_replicas",
                    "max_replicas",
                ],
                catalog_sku_roles=["cpu"],
                derivation=(
                    "Estimate active replica-seconds from request volume and duration, "
                    "bounded by min/max replicas, then multiply by cpu."
                ),
            ),
            CalculatedSkuDefinition(
                key="memory_gb_seconds",
                description="Billable GiB-seconds for allocated memory while replicas are active.",
                unit="GiB-seconds/month",
                input_keys=[
                    "requests_per_month",
                    "avg_request_duration_seconds",
                    "memory_gb",
                    "min_replicas",
                    "max_replicas",
                ],
                catalog_sku_roles=["memory"],
                derivation=(
                    "Same active replica-seconds as vcpu_seconds, multiplied by memory_gb."
                ),
            ),
            CalculatedSkuDefinition(
                key="requests",
                description="HTTP request count when a per-request meter applies.",
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
            min_resources={"cpu": 0.25, "memory_gb": 0.5, "min_replicas": 0},
            max_resources={"cpu": 4, "memory_gb": 8, "max_replicas": 30},
        ),
        default_values={
            "avg_request_duration_seconds": 0.25,
            "cpu": 0.5,
            "memory_gb": 1.0,
            "network_egress_gb": 0,
            "min_replicas": 0,
            "max_replicas": 10,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "requests": 2_000_000,
                "vcpu_seconds": 180_000,
                "memory_gb_seconds": 360_000,
            },
            notes="Consumption plan monthly free grant per subscription.",
        ),
        billing_unit="vCPU-seconds and GiB-seconds",
        billing_granularity="per second of active replica time; egress per GB",
        notes=[
            "Consumption plan pricing applies when min_replicas is 0.",
            "Dedicated workload profiles use separate compute meters not covered here.",
        ],
        warnings=[
            "Replica concurrency and idle-minimum replicas materially affect compute SKUs.",
            "Free tier grants are shared at the subscription level and may be partially consumed.",
        ],
    ),
)

_AZURE_SQL_DATABASE = AzureServicePricingModel(
    cloud="azure",
    service="Azure SQL Database",
    component_types=["database"],
    catalog_service_name="SQL Database",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="tier",
                description="Service tier family (e.g. General Purpose, Business Critical).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="General Purpose",
            ),
            UsageInputDefinition(
                key="compute_model",
                description="Provisioned capacity or serverless auto-pause compute.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="provisioned",
            ),
            UsageInputDefinition(
                key="vcores",
                description="Provisioned vCore count for the database.",
                unit="vCore",
                data_type=InputDataType.integer,
                min_value=1,
                max_value=80,
                default_value=2,
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="User database storage allocated.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=1,
                max_value=4096,
                default_value=32,
            ),
            UsageInputDefinition(
                key="backup_storage_gb",
                description="Long-term backup retention storage beyond included allowance.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="hours_per_month",
                description="Billable compute hours when the database is online.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="compute_hours",
                description="Database compute charged per vCore-hour.",
                unit="vCore-hours/month",
                input_keys=["vcores", "hours_per_month", "tier", "compute_model"],
                catalog_sku_roles=["cpu"],
                derivation="vcores * hours_per_month for provisioned compute.",
            ),
            CalculatedSkuDefinition(
                key="storage_gb_months",
                description="Allocated data storage.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="backup_storage_gb_months",
                description="Backup retention storage beyond included quota.",
                unit="GB-months",
                input_keys=["backup_storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from backup_storage_gb.",
            ),
        ],
        resource_rules=ResourceRules(
            min_resources={"vcores": 1, "storage_gb": 1},
            max_resources={"vcores": 80, "storage_gb": 4096},
            extra={"serverless_min_vcores": 0.5, "serverless_max_vcores": 40},
        ),
        default_values={
            "tier": "General Purpose",
            "compute_model": "provisioned",
            "vcores": 2,
            "storage_gb": 32,
            "backup_storage_gb": 0,
            "hours_per_month": 730,
        },
        free_tier=FreeTierAllowance(
            allowances={},
            notes="No always-free SQL Database tier; Azure free account credits may apply separately.",
        ),
        billing_unit="vCore-hours and GB-months",
        billing_granularity="compute per hour; storage per GB-month",
        notes=[
            "DTU-based SKUs are legacy; this model targets vCore-based tiers.",
            "Serverless compute uses per-second billing while online and a separate auto-pause model.",
        ],
        warnings=[
            "High availability replicas and zone redundancy add compute/storage multipliers.",
            "Backup storage beyond the tier allowance is billed separately.",
        ],
    ),
)

_AZURE_BLOB_STORAGE = AzureServicePricingModel(
    cloud="azure",
    service="Azure Blob Storage",
    component_types=["object_storage"],
    catalog_service_name="Blob Storage",
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
                key="access_tier",
                description="Hot, Cool, Cold, or Archive access tier.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Hot",
            ),
            UsageInputDefinition(
                key="redundancy",
                description="Replication option (LRS, ZRS, GRS, GZRS).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="LRS",
            ),
            UsageInputDefinition(
                key="write_operations",
                description="PUT, create, and write-type operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="read_operations",
                description="GET and read/list-type operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="list_operations",
                description="List and enumerate blob container operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
                required=False,
            ),
            UsageInputDefinition(
                key="data_retrieval_gb",
                description="Data read from Cool/Cold/Archive tiers.",
                unit="GB/month",
                data_type=InputDataType.float,
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
                key="storage_gb_months",
                description="Stored data capacity by tier and redundancy.",
                unit="GB-months",
                input_keys=["storage_gb", "access_tier", "redundancy"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb for the selected tier/redundancy.",
            ),
            CalculatedSkuDefinition(
                key="write_operations",
                description="Write operation count billed per 10k operations.",
                unit="operations/month",
                input_keys=["write_operations", "access_tier"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from write_operations.",
            ),
            CalculatedSkuDefinition(
                key="read_operations",
                description="Read operation count billed per 10k operations.",
                unit="operations/month",
                input_keys=["read_operations", "access_tier"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from read_operations.",
            ),
            CalculatedSkuDefinition(
                key="list_operations",
                description="List and enumerate blob container operations.",
                unit="operations/month",
                input_keys=["list_operations", "access_tier"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from list_operations.",
            ),
            CalculatedSkuDefinition(
                key="retrieval_gb",
                description="Data retrieval from non-hot tiers.",
                unit="GB/month",
                input_keys=["data_retrieval_gb", "access_tier"],
                catalog_sku_roles=["egress"],
                derivation="Direct mapping from data_retrieval_gb.",
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
            "access_tier": "Hot",
            "redundancy": "LRS",
            "write_operations": 0,
            "read_operations": 0,
            "list_operations": 0,
            "data_retrieval_gb": 0,
            "data_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "storage_gb_months": 5,
                "write_operations": 20_000,
                "read_operations": 20_000,
            },
            notes="First 5 GB LRS hot block blob storage and limited operations per month.",
        ),
        billing_unit="GB-months and per-10k operations",
        billing_granularity="storage per GB-month; operations per 10,000",
        notes=[
            "Archive tier adds rehydration latency and separate early deletion charges.",
            "Lifecycle transitions may incur additional operation charges.",
        ],
        warnings=[
            "Geo-redundant options multiply storage cost versus LRS.",
            "Free tier applies to specific LRS hot blob types only.",
        ],
    ),
)

_AZURE_QUEUE_STORAGE = AzureServicePricingModel(
    cloud="azure",
    service="Azure Queue Storage",
    component_types=["queue"],
    catalog_service_name="Queue Storage",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="storage_gb",
                description="Average queue message payload storage retained in the account.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="queue_operations",
                description="Enqueue, dequeue, and delete operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="data_egress_gb",
                description="Outbound data transfer when messages leave the region/account.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="storage_gb_months",
                description="Stored queue payload capacity.",
                unit="GB-months",
                input_keys=["storage_gb"],
                catalog_sku_roles=["storage"],
                derivation="Direct mapping from storage_gb.",
            ),
            CalculatedSkuDefinition(
                key="queue_operations",
                description="Queue transactions billed per 10k operations.",
                unit="operations/month",
                input_keys=["queue_operations"],
                catalog_sku_roles=["queue"],
                derivation="Direct mapping from queue_operations.",
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
        default_values={"storage_gb": 1, "data_egress_gb": 0},
        free_tier=FreeTierAllowance(
            allowances={
                "storage_gb_months": 5,
                "queue_operations": 20_000,
            },
            notes="Shares storage account free tier with other storage services.",
        ),
        billing_unit="GB-months and per-10k operations",
        billing_granularity="storage per GB-month; operations per 10,000",
        notes=[
            "Best for simple, high-volume background job buffering.",
            "No native pub/sub fan-out; consumers poll or trigger on messages.",
        ],
        warnings=[
            "Large message bodies increase storage_gb and egress_gb quickly.",
            "Visibility timeout retries can inflate queue_operations.",
        ],
    ),
)

_AZURE_SERVICE_BUS = AzureServicePricingModel(
    cloud="azure",
    service="Azure Service Bus",
    component_types=["queue"],
    catalog_service_name="Service Bus",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="messaging_tier",
                description="Basic, Standard, or Premium messaging tier.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Standard",
            ),
            UsageInputDefinition(
                key="hours_per_month",
                description="Billable hours the namespace is provisioned.",
                unit="hours/month",
                data_type=InputDataType.float,
                min_value=0,
                max_value=744,
                default_value=730,
            ),
            UsageInputDefinition(
                key="messaging_units",
                description="Premium messaging units (1, 2, 4, 8, 16). Ignored for Basic/Standard.",
                unit="MU",
                data_type=InputDataType.integer,
                min_value=1,
                max_value=16,
                default_value=1,
                required=False,
            ),
            UsageInputDefinition(
                key="queue_operations",
                description="Send/receive operations across queues and topics.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
            ),
            UsageInputDefinition(
                key="brokered_connections",
                description="Concurrent AMQP/HTTPS connections (Standard tier).",
                unit="connections",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
                required=False,
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
                key="namespace_months",
                description="Basic/Standard flat namespace charge.",
                unit="namespace-months",
                input_keys=["messaging_tier"],
                catalog_sku_roles=["namespace"],
                derivation="1 namespace-month for Basic/Standard tiers.",
            ),
            CalculatedSkuDefinition(
                key="messaging_unit_hours",
                description="Premium tier capacity units billed hourly.",
                unit="MU-hours/month",
                input_keys=["messaging_tier", "messaging_units", "hours_per_month"],
                catalog_sku_roles=["cpu"],
                derivation="messaging_units * hours_per_month when tier is Premium.",
            ),
            CalculatedSkuDefinition(
                key="queue_operations",
                description="Standard/Basic operation charges beyond included operations.",
                unit="operations/month",
                input_keys=["queue_operations", "messaging_tier"],
                catalog_sku_roles=["queue"],
                derivation="Direct mapping from queue_operations.",
            ),
            CalculatedSkuDefinition(
                key="brokered_connections",
                description="Additional brokered connections on Standard tier.",
                unit="connections/month",
                input_keys=["brokered_connections", "messaging_tier"],
                catalog_sku_roles=["requests"],
                derivation="Billable connections above tier allowance.",
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
            min_resources={"messaging_units": 1},
            max_resources={"messaging_units": 16},
            extra={"standard_base_operations": 13_000_000},
        ),
        default_values={
            "messaging_tier": "Standard",
            "hours_per_month": 730,
            "messaging_units": 1,
            "brokered_connections": 0,
            "data_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={"queue_operations": 13_000_000},
            notes="Standard tier includes 13M operations/month before overage meters.",
        ),
        billing_unit="operations, MU-hours, and connections",
        billing_granularity="Premium MU per hour; Standard operations per million",
        notes=[
            "Premium tier is required for VNet isolation and larger message sizes.",
            "Topics/subscriptions share the same operation meters as queues.",
        ],
        warnings=[
            "Premium tier has a minimum messaging unit charge even at low traffic.",
            "Basic tier lacks topics/subscriptions and has lower throughput limits.",
        ],
    ),
)

_AZURE_FUNCTIONS = AzureServicePricingModel(
    cloud="azure",
    service="Azure Functions",
    component_types=["service", "worker"],
    catalog_service_name="Functions",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="plan",
                description="Consumption, Premium (Elastic Premium), or Dedicated (App Service) plan.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="consumption",
            ),
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
                description="Memory configured for the function app.",
                unit="MB",
                data_type=InputDataType.integer,
                min_value=128,
                max_value=1536,
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
                key="executions",
                description="Billable invocation count.",
                unit="executions/month",
                input_keys=["executions_per_month"],
                catalog_sku_roles=["execution"],
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
                catalog_sku_roles=["memory"],
                derivation=(
                    "executions_per_month * (avg_execution_duration_ms / 1000) * (memory_mb / 1024)"
                ),
            ),
            CalculatedSkuDefinition(
                key="vcpu_hours",
                description="Premium plan vCPU duration when applicable.",
                unit="vCPU-hours/month",
                input_keys=["plan", "executions_per_month", "avg_execution_duration_ms"],
                catalog_sku_roles=["cpu"],
                derivation="Premium plan only: total execution vCPU-hours.",
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
            max_resources={"memory_mb": 1536},
            extra={"consumption_max_duration_minutes": 10},
        ),
        default_values={
            "plan": "consumption",
            "avg_execution_duration_ms": 200,
            "memory_mb": 512,
            "network_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "executions": 1_000_000,
                "gb_seconds": 400_000,
            },
            notes="Consumption plan monthly free grant per subscription.",
        ),
        billing_unit="executions and GB-seconds",
        billing_granularity="per execution; GB-seconds per 128 MB-s block on consumption",
        notes=[
            "Timer, HTTP, and queue-triggered functions share the same execution meters.",
            "Dedicated App Service plan bills the underlying plan separately.",
        ],
        warnings=[
            "Premium plan replaces GB-second metering with instance-based vCPU/memory charges.",
            "Always-on or minimum instances on Premium reduce scale-to-zero savings.",
        ],
    ),
)

from app.pricing.azure.definitions_extended import EXTENDED_AZURE_PRICING_MODELS
from app.pricing.azure.definitions_platform import PLATFORM_AZURE_PRICING_MODELS

AZURE_PRICING_MODELS: tuple[AzureServicePricingModel, ...] = (
    _AZURE_CONTAINER_APPS,
    _AZURE_SQL_DATABASE,
    _AZURE_BLOB_STORAGE,
    _AZURE_QUEUE_STORAGE,
    _AZURE_SERVICE_BUS,
    _AZURE_FUNCTIONS,
    *PLATFORM_AZURE_PRICING_MODELS,
    *EXTENDED_AZURE_PRICING_MODELS,
)
