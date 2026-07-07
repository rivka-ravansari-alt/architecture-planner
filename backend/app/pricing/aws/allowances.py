"""SKU key mapping and free-tier pool definitions for AWS pricing."""

from __future__ import annotations

SKU_ALLOWANCE_KEYS: dict[str, dict[str, str]] = {
    "Lambda": {
        "requests": "requests",
        "gb_seconds": "gb_seconds",
    },
    "S3": {
        "storage_gb_month": "storage_gb_month",
        "requests": "requests",
    },
    "SQS": {
        "requests": "requests",
    },
    "RDS": {
        "instance_hours": "instance_hours",
        "storage_gb_month": "storage_gb_month",
    },
    "DynamoDB": {
        "storage_gb_month": "storage_gb_month",
        "read_requests": "read_requests",
        "write_requests": "write_requests",
    },
    "API Gateway": {
        "requests": "requests",
    },
    "SNS": {
        "requests": "requests",
    },
    "CloudFront": {
        "requests": "requests",
    },
    "Application Load Balancer": {
        "lb_hours": "lb_hours",
        "lcu_hours": "lcu_hours",
    },
    "Secrets Manager": {
        "secret_months": "secret_months",
        "requests": "requests",
    },
    "SES": {"requests": "requests"},
    "CloudWatch": {
        "custom_metrics": "custom_metrics",
        "requests": "requests",
    },
    "CloudWatch Logs": {
        "ingestion_gb": "ingestion_gb",
        "storage_gb_month": "storage_gb_month",
    },
    "CloudWatch Dashboards": {"dashboard_hours": "dashboard_hours"},
    "CloudWatch Alarms": {
        "alarms": "alarms",
        "requests": "requests",
    },
    "SSM Parameter Store": {
        "parameter_months": "parameter_months",
        "requests": "requests",
    },
    "X-Ray": {"traces_ingested": "traces_ingested"},
}

FREE_TIER_POOLS: dict[str, list[str]] = {
    "aws_lambda_free": ["Lambda"],
    "aws_s3_free": ["S3"],
    "aws_sqs_free": ["SQS"],
    "aws_rds_free": ["RDS"],
    "aws_dynamodb_free": ["DynamoDB"],
    "aws_api_gateway_free": ["API Gateway"],
    "aws_sns_free": ["SNS"],
    "aws_ses_free": ["SES"],
    "aws_cloudwatch_free": ["CloudWatch"],
    "aws_cloudwatch_logs_free": ["CloudWatch Logs"],
    "aws_cloudwatch_dashboards_free": ["CloudWatch Dashboards"],
    "aws_cloudwatch_alarms_free": ["CloudWatch Alarms"],
    "aws_ssm_free": ["SSM Parameter Store"],
    "aws_xray_free": ["X-Ray"],
}

POOL_FREE_TIER_ALLOWANCES: dict[str, dict[str, float]] = {
    "aws_lambda_free": {
        "requests": 1_000_000,
        "gb_seconds": 400_000,
    },
    "aws_s3_free": {
        "storage_gb_month": 5,
        "requests": 20_000,
    },
    "aws_sqs_free": {
        "requests": 1_000_000,
    },
    "aws_rds_free": {
        "instance_hours": 750,
        "storage_gb_month": 20,
    },
    "aws_dynamodb_free": {
        "storage_gb_month": 25,
        "read_requests": 200_000_000,
        "write_requests": 200_000_000,
    },
    "aws_api_gateway_free": {
        "requests": 1_000_000,
    },
    "aws_sns_free": {
        "requests": 1_000_000,
    },
    "aws_ses_free": {
        "requests": 3_000,
    },
    "aws_cloudwatch_free": {
        "custom_metrics": 10,
        "requests": 1_000_000,
    },
    "aws_cloudwatch_logs_free": {
        "ingestion_gb": 5,
        "storage_gb_month": 5,
    },
    "aws_cloudwatch_dashboards_free": {
        "dashboard_hours": 730,
    },
    "aws_cloudwatch_alarms_free": {
        "alarms": 10,
    },
    "aws_ssm_free": {
        "parameter_months": 10_000,
        "requests": 1_000_000,
    },
    "aws_xray_free": {
        "traces_ingested": 100_000,
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
