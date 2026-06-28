"""Default component catalog entries seeded into architecture_components."""

from __future__ import annotations

from app.config.params import COMPONENT_CATEGORY_MAIN, COMPONENT_CATEGORY_SUPPORTING

_AZURE_APP_SERVICE = {
    "name": "Azure App Service",
    "api_service_name": "Azure App Service",
    "price_filter": "contains(productName, 'Static Web')",
}
_AZURE_BLOB_STORAGE = {
    "name": "Blob Storage",
    "api_service_name": "Storage",
    "price_filter": "contains(productName, 'Blob')",
}
_AZURE_QUEUE_STORAGE = {
    "name": "Queue Storage",
    "api_service_name": "Storage",
    "price_filter": "contains(productName, 'Queue')",
}

_AWS_AMPLIFY = {"name": "Amplify", "api_service_code": "AWSAmplify"}
_AWS_AMPLIFY_HOSTING = {"name": "Amplify Hosting", "api_service_code": "AWSAmplify"}
_AWS_CLOUDFRONT = {"name": "CloudFront", "api_service_code": "AmazonCloudFront"}
_AWS_ALB = {
    "name": "Application Load Balancer",
    "api_service_code": "AWSELB",
    "attribute_filters": [{"field": "usagetype", "value": "LoadBalancerUsage"}],
}
_AWS_API_GATEWAY = {"name": "API Gateway", "api_service_code": "AmazonApiGateway"}
_AWS_LAMBDA = {"name": "Lambda", "api_service_code": "AWSLambda"}
_AWS_ECS_FARGATE = {
    "name": "ECS Fargate",
    "api_service_code": "AmazonECS",
    "attribute_filters": [{"field": "usagetype", "value": "Fargate"}],
}
_AWS_DYNAMODB = {"name": "DynamoDB", "api_service_code": "AmazonDynamoDB"}
_AWS_RDS = {"name": "RDS", "api_service_code": "AmazonRDS"}
_AWS_ELASTICACHE = {"name": "ElastiCache", "api_service_code": "AmazonElastiCache"}
_AWS_SQS = {"name": "SQS", "api_service_code": "AWSQueueService"}
_AWS_S3 = {"name": "S3", "api_service_code": "AmazonS3"}
_AWS_OPENSEARCH = {"name": "OpenSearch Service", "api_service_code": "AmazonES"}
_AWS_BEDROCK = {"name": "Bedrock", "api_service_code": "AmazonBedrock"}
_AWS_SNS = {"name": "SNS", "api_service_code": "AmazonSNS"}
_AWS_SES = {"name": "SES", "api_service_code": "AmazonSES"}
_AWS_CLOUDWATCH = {"name": "CloudWatch", "api_service_code": "AmazonCloudWatch"}
_AWS_CLOUDWATCH_LOGS = {
    "name": "CloudWatch Logs",
    "api_service_code": "AmazonCloudWatch",
    "attribute_filters": [{"field": "group", "value": "Ingested Logs", "match": "equals"}],
}
_AWS_CLOUDWATCH_DASHBOARDS = {
    "name": "CloudWatch Dashboards",
    "api_service_code": "AmazonCloudWatch",
    "attribute_filters": [{"field": "group", "value": "Metric", "match": "equals"}],
}
_AWS_CLOUDWATCH_ALARMS = {
    "name": "CloudWatch Alarms",
    "api_service_code": "AmazonCloudWatch",
    "attribute_filters": [{"field": "group", "value": "Alarm"}],
}
_AWS_ATHENA = {"name": "Athena", "api_service_code": "AmazonAthena"}
_AWS_QUICKSIGHT = {"name": "QuickSight", "api_service_code": "AmazonQuickSight"}
_AWS_SECRETS_MANAGER = {"name": "Secrets Manager", "api_service_code": "AWSSecretsManager"}
_AWS_SSM = {
    "name": "SSM Parameter Store",
    "api_service_code": "AWSSystemsManager",
    "attribute_filters": [{"field": "usagetype", "value": "PS-Param", "match": "contains"}],
}
_AWS_APPCONFIG = {
    "name": "AppConfig",
    "api_service_code": "AWSSystemsManager",
    "attribute_filters": [{"field": "usagetype", "value": "AppConfig", "match": "contains"}],
}
_AWS_XRAY = {"name": "X-Ray", "api_service_code": "AWSXRay"}

_COMPONENTS: list[tuple[str, str, str, list, list[str], list]] = [
    (
        "user",
        COMPONENT_CATEGORY_MAIN,
        "End users who interact with the product through client applications.",
        ["N/A"],
        ["N/A"],
        ["N/A"],
    ),
    (
        "web_app",
        COMPONENT_CATEGORY_MAIN,
        "Browser-based application that delivers the primary user experience.",
        [_AWS_AMPLIFY_HOSTING],
        ["Firebase Hosting"],
        [_AZURE_APP_SERVICE],
    ),
    (
        "mobile_app",
        COMPONENT_CATEGORY_MAIN,
        "Native or cross-platform mobile application for iOS and Android devices.",
        [_AWS_AMPLIFY],
        ["Firebase"],
        ["Azure App Center"],
    ),
    (
        "admin_panel",
        COMPONENT_CATEGORY_MAIN,
        "Administrative interface for managing users, content, and configuration.",
        [_AWS_AMPLIFY_HOSTING],
        ["Firebase Hosting"],
        [_AZURE_APP_SERVICE],
    ),
    (
        "cdn",
        COMPONENT_CATEGORY_MAIN,
        "Content delivery network that caches and serves static assets close to users.",
        [_AWS_CLOUDFRONT],
        ["Networking"],
        ["Content Delivery Network"],
    ),
    (
        "load_balancer",
        COMPONENT_CATEGORY_MAIN,
        "Distributes incoming traffic across service instances for availability and scale.",
        [_AWS_ALB],
        ["Networking"],
        ["Application Gateway"],
    ),
    (
        "api_gateway",
        COMPONENT_CATEGORY_MAIN,
        "Entry point for client requests. Routes traffic to backend services and may apply authentication or rate limiting. It does not execute business logic, access databases, or replace a backend service.",
        [_AWS_API_GATEWAY],
        ["API Gateway"],
        ["API Management"],
    ),
    (
        "service",
        COMPONENT_CATEGORY_MAIN,
        "Backend execution component that implements business logic, exposes application APIs, processes user requests, and reads/writes application data.",
        [_AWS_LAMBDA, _AWS_ECS_FARGATE],
        ["Cloud Run", "Cloud Run Functions"],
        ["Functions", "Azure Container Apps"],
    ),
    (
        "worker",
        COMPONENT_CATEGORY_MAIN,
        "Background processor that handles asynchronous jobs and long-running tasks.",
        [_AWS_LAMBDA, _AWS_ECS_FARGATE],
        ["Cloud Run", "Cloud Run Functions"],
        ["Functions", "Azure Container Apps"],
    ),
    (
        "database",
        COMPONENT_CATEGORY_MAIN,
        "Primary data store for structured application data and transactions.",
        [_AWS_DYNAMODB, _AWS_RDS],
        ["Cloud Firestore", "Cloud SQL"],
        ["Azure Cosmos DB", "SQL Database"],
    ),
    (
        "cache",
        COMPONENT_CATEGORY_MAIN,
        "In-memory store that reduces database load and improves read latency.",
        [_AWS_ELASTICACHE],
        ["Cloud Memorystore for Redis"],
        ["Redis Cache"],
    ),
    (
        "queue",
        COMPONENT_CATEGORY_MAIN,
        "Message queue that decouples producers and consumers for reliable async processing.",
        [_AWS_SQS],
        ["Cloud Pub/Sub", "Cloud Tasks"],
        ["Service Bus", _AZURE_QUEUE_STORAGE],
    ),
    (
        "object_storage",
        COMPONENT_CATEGORY_MAIN,
        "Durable storage for files, images, uploads, and other unstructured data.",
        [_AWS_S3],
        ["Cloud Storage"],
        [_AZURE_BLOB_STORAGE],
    ),
    (
        "search",
        COMPONENT_CATEGORY_MAIN,
        "Full-text search index for fast querying across application content.",
        [_AWS_OPENSEARCH],
        ["Vertex AI Search"],
        ["Azure Cognitive Search"],
    ),
    (
        "external_api",
        COMPONENT_CATEGORY_MAIN,
        "Integration with third-party services and partner APIs.",
        ["Third-party API"],
        ["Third-party API"],
        ["Third-party API"],
    ),
    (
        "ai_provider",
        COMPONENT_CATEGORY_MAIN,
        "External or managed AI/ML service for inference, embeddings, or generative features.",
        [_AWS_BEDROCK],
        ["Gemini API", "Vertex AI"],
        ["Foundry Models"],
    ),
    (
        "payment",
        COMPONENT_CATEGORY_MAIN,
        "Payment processing for subscriptions, one-time purchases, and billing.",
        ["Stripe", "Paddle"],
        ["Stripe", "Paddle"],
        ["Stripe", "Paddle"],
    ),
    (
        "notification",
        COMPONENT_CATEGORY_MAIN,
        "Delivers email, SMS, and push notifications to users.",
        [_AWS_SNS, _AWS_SES],
        ["Firebase", "SendGrid"],
        ["Notification Hubs", "Voice Core"],
    ),
    (
        "analytics",
        COMPONENT_CATEGORY_MAIN,
        "Collects usage data and supports reporting, dashboards, and product insights.",
        [_AWS_CLOUDWATCH_DASHBOARDS, _AWS_ATHENA, _AWS_QUICKSIGHT],
        ["Looker Studio", "BigQuery"],
        ["Application Insights", "Power BI"],
    ),
    (
        "secrets",
        COMPONENT_CATEGORY_SUPPORTING,
        "Secure storage and rotation of API keys, credentials, and sensitive configuration.",
        [_AWS_SECRETS_MANAGER, _AWS_SSM],
        ["Secret Manager"],
        ["Key Vault"],
    ),
    (
        "config",
        COMPONENT_CATEGORY_SUPPORTING,
        "Centralized configuration management across environments and services.",
        [_AWS_APPCONFIG, _AWS_SSM],
        ["Secret Manager", "Cloud Firestore"],
        ["App Configuration"],
    ),
    (
        "monitoring",
        COMPONENT_CATEGORY_SUPPORTING,
        "Tracks health, performance metrics, and service-level indicators.",
        [_AWS_CLOUDWATCH],
        ["Cloud Monitoring"],
        ["Azure Monitor"],
    ),
    (
        "logging",
        COMPONENT_CATEGORY_SUPPORTING,
        "Aggregates application and infrastructure logs for troubleshooting.",
        [_AWS_CLOUDWATCH_LOGS],
        ["Cloud Logging"],
        ["Log Analytics"],
    ),
    (
        "tracing",
        COMPONENT_CATEGORY_SUPPORTING,
        "Distributed tracing to follow requests across services and diagnose latency.",
        [_AWS_XRAY],
        ["Cloud Trace"],
        ["Application Insights"],
    ),
    (
        "alerting",
        COMPONENT_CATEGORY_SUPPORTING,
        "Routes monitoring signals to on-call channels when thresholds are breached.",
        [_AWS_CLOUDWATCH_ALARMS, _AWS_SNS],
        ["Cloud Monitoring"],
        ["Azure Monitor"],
    ),
]

COMPONENT_CATALOG_SEED: list[dict[str, object]] = [
    {
        "name": name,
        "category": category,
        "description": description,
        "aws_options": aws_options,
        "gcp_options": gcp_options,
        "azure_options": azure_options,
    }
    for name, category, description, aws_options, gcp_options, azure_options in _COMPONENTS
]
