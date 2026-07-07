"""AWS service pricing model definitions.

These models describe which usage inputs are needed to derive billable SKUs.
Unit prices come from the Firestore aws_catalog — not from the LLM.
"""

from __future__ import annotations

from app.pricing.schemas import (
    AwsServicePricingModel,
    CalculatedSkuDefinition,
    FreeTierAllowance,
    InputDataType,
    PricingModelDetails,
    ResourceRules,
    UsageInputDefinition,
)

_AWS_LAMBDA = AwsServicePricingModel(
    cloud="aws",
    service="Lambda",
    component_types=["service", "worker"],
    catalog_service_name="Lambda",
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
                max_value=10240,
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
                catalog_sku_roles=["duration"],
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
            max_resources={"memory_mb": 10240},
        ),
        default_values={
            "avg_execution_duration_ms": 200,
            "memory_mb": 512,
            "network_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "requests": 1_000_000,
                "gb_seconds": 400_000,
            },
            notes="AWS Free Tier: 1M requests and 400K GB-seconds per month.",
        ),
        billing_unit="requests and GB-seconds",
        billing_granularity="per request; GB-seconds per 128 MB-s block",
        notes=[
            "Timer, HTTP, and queue-triggered functions share the same execution meters.",
        ],
        warnings=[
            "Provisioned concurrency and Lambda@Edge add separate meters not covered here.",
        ],
    ),
)

_AWS_ECS_FARGATE = AwsServicePricingModel(
    cloud="aws",
    service="ECS Fargate",
    component_types=["service", "worker"],
    catalog_service_name="ECS Fargate",
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
                description="vCPU cores allocated per task.",
                unit="vCPU",
                data_type=InputDataType.float,
                min_value=0.25,
                max_value=4,
                default_value=0.5,
            ),
            UsageInputDefinition(
                key="memory_gb",
                description="Memory allocated per task.",
                unit="GiB",
                data_type=InputDataType.float,
                min_value=0.5,
                max_value=30,
                default_value=1.0,
            ),
            UsageInputDefinition(
                key="network_egress_gb",
                description="Outbound data transfer from tasks.",
                unit="GB/month",
                data_type=InputDataType.float,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="min_tasks",
                description="Minimum number of running tasks (0 enables scale-to-zero).",
                unit="tasks",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
        ],
        calculated_skus=[
            CalculatedSkuDefinition(
                key="vcpu_hours",
                description="Billable vCPU-hours across active task time.",
                unit="vCPU-hours/month",
                input_keys=[
                    "requests_per_month",
                    "avg_request_duration_seconds",
                    "cpu",
                    "min_tasks",
                ],
                catalog_sku_roles=["cpu"],
                derivation=(
                    "max(requests * duration * cpu / 3600, min_tasks * cpu * hours_per_month)"
                ),
            ),
            CalculatedSkuDefinition(
                key="memory_gb_hours",
                description="Billable GiB-hours for allocated memory while tasks are active.",
                unit="GiB-hours/month",
                input_keys=[
                    "requests_per_month",
                    "avg_request_duration_seconds",
                    "memory_gb",
                    "min_tasks",
                ],
                catalog_sku_roles=["memory"],
                derivation=(
                    "max(requests * duration * memory_gb / 3600, "
                    "min_tasks * memory_gb * hours_per_month)"
                ),
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
            min_resources={"cpu": 0.25, "memory_gb": 0.5, "min_tasks": 0},
            max_resources={"cpu": 4, "memory_gb": 30},
        ),
        default_values={
            "avg_request_duration_seconds": 0.25,
            "cpu": 0.5,
            "memory_gb": 1.0,
            "network_egress_gb": 0,
            "min_tasks": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={},
            notes="ECS Fargate has no always-free tier; AWS Free Tier credits may apply separately.",
        ),
        billing_unit="vCPU-hours and GiB-hours",
        billing_granularity="per hour of task runtime; egress per GB",
        notes=[
            "Fargate Spot and Savings Plans are not modeled in v1.",
        ],
        warnings=[
            "Minimum task count materially affects compute SKUs when scale-to-zero is disabled.",
        ],
    ),
)

_AWS_RDS = AwsServicePricingModel(
    cloud="aws",
    service="RDS",
    component_types=["database"],
    catalog_service_name="RDS",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="instance_class",
                description="RDS instance class (e.g. db.t3.micro, db.t3.small).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="db.t3.micro",
            ),
            UsageInputDefinition(
                key="storage_gb",
                description="Allocated database storage.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=20,
                max_value=65536,
                default_value=20,
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
                input_keys=["hours_per_month", "instance_class"],
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
            min_resources={"storage_gb": 20},
            max_resources={"storage_gb": 65536},
        ),
        default_values={
            "instance_class": "db.t3.micro",
            "storage_gb": 20,
            "backup_storage_gb": 0,
            "hours_per_month": 730,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "instance_hours": 750,
                "storage_gb_month": 20,
            },
            notes="AWS Free Tier: 750 instance-hours and 20 GB storage for db.t2/db.t3.micro.",
        ),
        billing_unit="instance-hours and GB-months",
        billing_granularity="compute per hour; storage per GB-month",
        notes=[
            "Aurora and serverless v2 use different meters not covered in v1.",
        ],
        warnings=[
            "Multi-AZ deployments double instance-hour charges.",
        ],
    ),
)

_AWS_S3 = AwsServicePricingModel(
    cloud="aws",
    service="S3",
    component_types=["object_storage"],
    catalog_service_name="S3",
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
                description="S3 storage class (Standard, Standard-IA, etc.).",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Standard",
            ),
            UsageInputDefinition(
                key="write_operations",
                description="PUT, POST, and copy-type operations.",
                unit="operations/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="read_operations",
                description="GET and select-type operations.",
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
                "requests": 20_000,
            },
            notes="AWS Free Tier: 5 GB Standard storage and 20K GET + 2K PUT requests.",
        ),
        billing_unit="GB-months and per-1K requests",
        billing_granularity="storage per GB-month; requests per 1,000",
        notes=[
            "Intelligent-Tiering and Glacier add separate meters.",
        ],
        warnings=[
            "Cross-region replication multiplies storage and transfer costs.",
        ],
    ),
)

_AWS_SQS = AwsServicePricingModel(
    cloud="aws",
    service="SQS",
    component_types=["queue"],
    catalog_service_name="SQS",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="queue_type",
                description="Standard or FIFO queue.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="Standard",
            ),
            UsageInputDefinition(
                key="queue_operations",
                description="Send, receive, and delete API requests.",
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
                description="Queue API request count.",
                unit="operations/month",
                input_keys=["queue_operations", "queue_type"],
                catalog_sku_roles=["requests"],
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
        resource_rules=ResourceRules(extra={"fifo_multiplier": 1.25}),
        default_values={
            "queue_type": "Standard",
            "data_egress_gb": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={"requests": 1_000_000},
            notes="AWS Free Tier: 1M SQS requests per month.",
        ),
        billing_unit="requests",
        billing_granularity="per million requests",
        notes=[
            "FIFO queues have higher per-request pricing than Standard.",
        ],
        warnings=[
            "Long polling and batch operations affect request counts.",
        ],
    ),
)

_AWS_DYNAMODB = AwsServicePricingModel(
    cloud="aws",
    service="DynamoDB",
    component_types=["database"],
    catalog_service_name="DynamoDB",
    pricing_model=PricingModelDetails(
        required_inputs=[
            UsageInputDefinition(
                key="storage_gb",
                description="Average table storage during the month.",
                unit="GB",
                data_type=InputDataType.float,
                min_value=0,
                default_value=1,
            ),
            UsageInputDefinition(
                key="read_requests_per_month",
                description="On-demand read request units per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="write_requests_per_month",
                description="On-demand write request units per month.",
                unit="requests/month",
                data_type=InputDataType.integer,
                min_value=0,
                default_value=0,
            ),
            UsageInputDefinition(
                key="billing_mode",
                description="On-demand or provisioned capacity.",
                unit="enum",
                data_type=InputDataType.string,
                default_value="on_demand",
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
                description="On-demand read request units.",
                unit="requests/month",
                input_keys=["read_requests_per_month", "billing_mode"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from read_requests_per_month.",
            ),
            CalculatedSkuDefinition(
                key="write_requests",
                description="On-demand write request units.",
                unit="requests/month",
                input_keys=["write_requests_per_month", "billing_mode"],
                catalog_sku_roles=["requests"],
                derivation="Direct mapping from write_requests_per_month.",
            ),
        ],
        resource_rules=ResourceRules(min_resources={"storage_gb": 0}),
        default_values={
            "billing_mode": "on_demand",
            "read_requests_per_month": 0,
            "write_requests_per_month": 0,
        },
        free_tier=FreeTierAllowance(
            allowances={
                "storage_gb_month": 25,
                "read_requests": 200_000_000,
                "write_requests": 200_000_000,
            },
            notes="AWS Free Tier: 25 GB storage and 200M read/write request units per month.",
        ),
        billing_unit="GB-months and request units",
        billing_granularity="on-demand per million request units; storage per GB-month",
        notes=[
            "Provisioned capacity and global tables add separate meters not covered in v1.",
        ],
        warnings=[
            "Streams, backups, and PITR add meters not included in this model.",
        ],
    ),
)

from app.pricing.aws.definitions_platform import PLATFORM_AWS_PRICING_MODELS
from app.pricing.aws.definitions_extended import EXTENDED_AWS_PRICING_MODELS

AWS_PRICING_MODELS: tuple[AwsServicePricingModel, ...] = (
    _AWS_LAMBDA,
    _AWS_ECS_FARGATE,
    _AWS_RDS,
    _AWS_DYNAMODB,
    _AWS_S3,
    _AWS_SQS,
    *PLATFORM_AWS_PRICING_MODELS,
    *EXTENDED_AWS_PRICING_MODELS,
)
