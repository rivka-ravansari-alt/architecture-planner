"""Shared fake Firestore catalog fixtures for AWS cost tests."""

from __future__ import annotations

from app.pricing.aws.catalog_lookup import AwsCatalogLookup
from app.pricing.aws.cost_calculator import AwsCostCalculator
from app.pricing.aws.meter_scaling import AwsMeterUnitScaler
from app.pricing.aws.sku_roles import AwsSkuRoleResolver
from app.pricing_ingestion.models.documents import AwsCatalogRecord
from app.pricing_ingestion.repositories.aws_catalog_repository import AwsCatalogRepository
from app.pricing_ingestion.repositories.fake_firestore import FakeFirestoreClient
from app.utils.slug import slugify


class AwsCatalogTestFixture:
    """Seed fake Firestore with representative aws_catalog documents."""

    def __init__(self) -> None:
        self.client = FakeFirestoreClient()
        self.repo = AwsCatalogRepository(self.client)
        self._seed_standard_catalogs()

    def _seed_standard_catalogs(self) -> None:
        lambda_record = AwsCatalogRecord(
            id=slugify("Lambda"),
            name="Lambda",
            skus={
                "requests": {
                    "sku_id": "lambda-request",
                    "description": "AWS Lambda - Requests",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.0000002,
                },
                "duration": {
                    "sku_id": "lambda-duration",
                    "description": "AWS Lambda - GB-Seconds",
                    "usage_unit": "GB-Seconds",
                    "currency": "USD",
                    "unit_price_usd": 0.0000166667,
                },
                "egress": {
                    "sku_id": "lambda-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "requests_cost + duration_cost"},
        )
        s3_record = AwsCatalogRecord(
            id=slugify("S3"),
            name="S3",
            skus={
                "storage": {
                    "sku_id": "s3-storage",
                    "description": "Amazon S3 Standard storage",
                    "usage_unit": "GB-Mo",
                    "currency": "USD",
                    "unit_price_usd": 0.023,
                },
                "requests": {
                    "sku_id": "s3-requests",
                    "description": "S3 Requests",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.0000004,
                },
                "egress": {
                    "sku_id": "s3-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "storage_cost + requests_cost"},
        )
        rds_record = AwsCatalogRecord(
            id=slugify("RDS"),
            name="RDS",
            skus={
                "cpu": {
                    "sku_id": "rds-instance",
                    "description": "RDS db.t3.micro",
                    "usage_unit": "Hrs",
                    "currency": "USD",
                    "unit_price_usd": 0.017,
                },
                "storage": {
                    "sku_id": "rds-storage",
                    "description": "RDS Storage",
                    "usage_unit": "GB-Mo",
                    "currency": "USD",
                    "unit_price_usd": 0.115,
                },
            },
            formula={"total": "cpu_cost + storage_cost"},
        )
        sqs_record = AwsCatalogRecord(
            id=slugify("SQS"),
            name="SQS",
            skus={
                "requests": {
                    "sku_id": "sqs-requests",
                    "description": "SQS Requests",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.0000004,
                },
                "egress": {
                    "sku_id": "sqs-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "requests_cost + egress_cost"},
        )
        ecs_record = AwsCatalogRecord(
            id=slugify("ECS Fargate"),
            name="ECS Fargate",
            skus={
                "cpu": {
                    "sku_id": "fargate-cpu",
                    "description": "Fargate vCPU",
                    "usage_unit": "hours",
                    "currency": "USD",
                    "unit_price_usd": 0.04048,
                },
                "memory": {
                    "sku_id": "fargate-memory",
                    "description": "Fargate Memory",
                    "usage_unit": "hours",
                    "currency": "USD",
                    "unit_price_usd": 0.004445,
                },
                "egress": {
                    "sku_id": "fargate-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "cpu_cost + memory_cost"},
        )
        dynamodb_record = AwsCatalogRecord(
            id=slugify("DynamoDB"),
            name="DynamoDB",
            skus={
                "storage": {
                    "sku_id": "dynamodb-storage",
                    "description": "Amazon DynamoDB table storage",
                    "usage_unit": "GB-Mo",
                    "currency": "USD",
                    "unit_price_usd": 0.25,
                },
                "requests": {
                    "sku_id": "dynamodb-requests",
                    "description": "DynamoDB on-demand request units",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.00000025,
                },
            },
            formula={"total": "storage_cost + requests_cost"},
        )
        api_gateway_record = AwsCatalogRecord(
            id=slugify("API Gateway"),
            name="API Gateway",
            skus={
                "requests": {
                    "sku_id": "apigw-requests",
                    "description": "Amazon API Gateway HTTP API requests",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.000001,
                },
                "egress": {
                    "sku_id": "apigw-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "requests_cost + egress_cost"},
        )
        sns_record = AwsCatalogRecord(
            id=slugify("SNS"),
            name="SNS",
            skus={
                "requests": {
                    "sku_id": "sns-requests",
                    "description": "Amazon SNS publish/delivery requests",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.0000005,
                },
                "egress": {
                    "sku_id": "sns-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "requests_cost + egress_cost"},
        )
        cloudfront_record = AwsCatalogRecord(
            id=slugify("CloudFront"),
            name="CloudFront",
            skus={
                "requests": {
                    "sku_id": "cf-requests",
                    "description": "CloudFront HTTP/HTTPS requests",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.00000075,
                },
                "egress": {
                    "sku_id": "cf-egress",
                    "description": "CloudFront data transfer out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.085,
                },
            },
            formula={"total": "requests_cost + egress_cost"},
        )
        alb_record = AwsCatalogRecord(
            id=slugify("Application Load Balancer"),
            name="Application Load Balancer",
            skus={
                "cpu": {
                    "sku_id": "alb-hours",
                    "description": "Application Load Balancer hours",
                    "usage_unit": "Hrs",
                    "currency": "USD",
                    "unit_price_usd": 0.0225,
                },
                "memory": {
                    "sku_id": "alb-lcu",
                    "description": "Application Load Balancer LCU-hours",
                    "usage_unit": "LCU-Hrs",
                    "currency": "USD",
                    "unit_price_usd": 0.008,
                },
                "egress": {
                    "sku_id": "alb-egress",
                    "description": "Data Transfer Out",
                    "usage_unit": "GB",
                    "currency": "USD",
                    "unit_price_usd": 0.09,
                },
            },
            formula={"total": "cpu_cost + memory_cost + egress_cost"},
        )
        secrets_record = AwsCatalogRecord(
            id=slugify("Secrets Manager"),
            name="Secrets Manager",
            skus={
                "storage": {
                    "sku_id": "secrets-storage",
                    "description": "Secrets Manager secret-months",
                    "usage_unit": "Secret-Mo",
                    "currency": "USD",
                    "unit_price_usd": 0.40,
                },
                "requests": {
                    "sku_id": "secrets-requests",
                    "description": "Secrets Manager API calls",
                    "usage_unit": "Requests",
                    "currency": "USD",
                    "unit_price_usd": 0.00005,
                },
            },
            formula={"total": "storage_cost + requests_cost"},
        )
        extended_records = [
            AwsCatalogRecord(
                id=slugify(name),
                name=name,
                skus=skus,
                formula={"total": " + ".join(f"{role}_cost" for role in skus)},
            )
            for name, skus in (
                (
                    "Amplify",
                    {
                        "cpu": {"sku_id": "amplify-build", "description": "Build minutes", "usage_unit": "Minutes", "currency": "USD", "unit_price_usd": 0.01},
                        "requests": {"sku_id": "amplify-host", "description": "Hosting requests", "usage_unit": "Requests", "currency": "USD", "unit_price_usd": 0.0000002},
                        "egress": {"sku_id": "amplify-egress", "description": "Data transfer", "usage_unit": "GB", "currency": "USD", "unit_price_usd": 0.15},
                    },
                ),
                (
                    "Amplify Hosting",
                    {
                        "requests": {"sku_id": "amplify-hosting-req", "description": "Hosting requests", "usage_unit": "Requests", "currency": "USD", "unit_price_usd": 0.0000002},
                        "egress": {"sku_id": "amplify-hosting-egress", "description": "Data transfer", "usage_unit": "GB", "currency": "USD", "unit_price_usd": 0.15},
                        "cpu": {"sku_id": "amplify-hosting-build", "description": "Build minutes", "usage_unit": "Minutes", "currency": "USD", "unit_price_usd": 0.01},
                    },
                ),
                (
                    "Bedrock",
                    {
                        "requests": {"sku_id": "bedrock-input", "description": "Input tokens", "usage_unit": "1K Tokens", "currency": "USD", "unit_price_usd": 0.003},
                        "memory": {"sku_id": "bedrock-output", "description": "Output tokens", "usage_unit": "1K Tokens", "currency": "USD", "unit_price_usd": 0.015},
                    },
                ),
                (
                    "ElastiCache",
                    {
                        "cpu": {"sku_id": "elasticache-node", "description": "Node hours", "usage_unit": "Hrs", "currency": "USD", "unit_price_usd": 0.017},
                        "egress": {"sku_id": "elasticache-egress", "description": "Data transfer", "usage_unit": "GB", "currency": "USD", "unit_price_usd": 0.09},
                    },
                ),
                (
                    "OpenSearch Service",
                    {
                        "cpu": {"sku_id": "opensearch-instance", "description": "Instance hours", "usage_unit": "Hrs", "currency": "USD", "unit_price_usd": 0.036},
                        "storage": {"sku_id": "opensearch-storage", "description": "Storage", "usage_unit": "GB-Mo", "currency": "USD", "unit_price_usd": 0.135},
                        "egress": {"sku_id": "opensearch-egress", "description": "Data transfer", "usage_unit": "GB", "currency": "USD", "unit_price_usd": 0.09},
                    },
                ),
                (
                    "Athena",
                    {"storage": {"sku_id": "athena-scan", "description": "Data scanned", "usage_unit": "TB", "currency": "USD", "unit_price_usd": 5.0}},
                ),
                (
                    "QuickSight",
                    {
                        "requests": {"sku_id": "qs-reader", "description": "Reader seats", "usage_unit": "Seats", "currency": "USD", "unit_price_usd": 3.0},
                        "cpu": {"sku_id": "qs-author", "description": "Author seats", "usage_unit": "Seats", "currency": "USD", "unit_price_usd": 24.0},
                    },
                ),
                (
                    "SES",
                    {
                        "requests": {"sku_id": "ses-email", "description": "Emails sent", "usage_unit": "1K Emails", "currency": "USD", "unit_price_usd": 0.10},
                        "egress": {"sku_id": "ses-egress", "description": "Data transfer", "usage_unit": "GB", "currency": "USD", "unit_price_usd": 0.09},
                    },
                ),
                (
                    "CloudWatch",
                    {
                        "storage": {"sku_id": "cw-metrics", "description": "Custom metrics", "usage_unit": "Metrics", "currency": "USD", "unit_price_usd": 0.30},
                        "requests": {"sku_id": "cw-api", "description": "API requests", "usage_unit": "1M Requests", "currency": "USD", "unit_price_usd": 0.01},
                    },
                ),
                (
                    "CloudWatch Logs",
                    {
                        "requests": {"sku_id": "cwlogs-ingest", "description": "Log ingestion", "usage_unit": "GB", "currency": "USD", "unit_price_usd": 0.50},
                        "storage": {"sku_id": "cwlogs-storage", "description": "Log storage", "usage_unit": "GB-Mo", "currency": "USD", "unit_price_usd": 0.03},
                    },
                ),
                (
                    "CloudWatch Dashboards",
                    {"cpu": {"sku_id": "cw-dashboards", "description": "Dashboard hours", "usage_unit": "Dashboard-Hrs", "currency": "USD", "unit_price_usd": 0.01}},
                ),
                (
                    "CloudWatch Alarms",
                    {
                        "storage": {"sku_id": "cw-alarms", "description": "Standard alarms", "usage_unit": "Alarms", "currency": "USD", "unit_price_usd": 0.10},
                        "requests": {"sku_id": "cw-alarm-eval", "description": "Alarm evaluations", "usage_unit": "1M Requests", "currency": "USD", "unit_price_usd": 0.10},
                    },
                ),
                (
                    "SSM Parameter Store",
                    {
                        "storage": {"sku_id": "ssm-params", "description": "Parameters", "usage_unit": "Parameters", "currency": "USD", "unit_price_usd": 0.05},
                        "requests": {"sku_id": "ssm-api", "description": "API calls", "usage_unit": "10K Requests", "currency": "USD", "unit_price_usd": 0.05},
                    },
                ),
                (
                    "AppConfig",
                    {
                        "storage": {"sku_id": "appconfig-cfg", "description": "Configurations", "usage_unit": "Configurations", "currency": "USD", "unit_price_usd": 0.10},
                        "requests": {"sku_id": "appconfig-deploy", "description": "Deployment events", "usage_unit": "Requests", "currency": "USD", "unit_price_usd": 0.000002},
                        "use1_appconfig_experimenthours": {
                            "sku_id": "appconfig-exp",
                            "description": "AppConfig-ExperimentHours",
                            "usage_unit": "Hours",
                            "currency": "USD",
                            "unit_price_usd": 0.90,
                        },
                    },
                ),
                (
                    "X-Ray",
                    {
                        "requests": {"sku_id": "xray-ingest", "description": "Traces ingested", "usage_unit": "1M Traces", "currency": "USD", "unit_price_usd": 5.0},
                        "memory": {"sku_id": "xray-scan", "description": "Traces scanned", "usage_unit": "1M Traces", "currency": "USD", "unit_price_usd": 0.50},
                    },
                ),
            )
        ]
        for record in (
            lambda_record,
            s3_record,
            rds_record,
            sqs_record,
            ecs_record,
            dynamodb_record,
            api_gateway_record,
            sns_record,
            cloudfront_record,
            alb_record,
            secrets_record,
            *extended_records,
        ):
            self.repo.upsert(record)

    def build_cost_calculator(self) -> AwsCostCalculator:
        lookup = AwsCatalogLookup(self.repo)
        return AwsCostCalculator(lookup, AwsSkuRoleResolver(), AwsMeterUnitScaler())
