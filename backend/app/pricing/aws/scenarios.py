"""AWS platform benchmark scenarios exercising extended catalog services."""

from __future__ import annotations

from app.pricing.azure.scenarios import (
    ALL_BENCHMARK_SCENARIOS,
    ArchitectureComponentSpec,
    BenchmarkScenario,
    _comp,
    _mapped_components,
    _scenario,
)

# Five architectures that exercise newly implemented AWS platform / observability services.
AWS_PLATFORM_BENCHMARK_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    _scenario(
        "mobile_wellness",
        "Mobile Wellness App",
        (
            "A cross-platform mobile app for daily wellness check-ins, streak tracking, "
            "and push reminders. Static assets and the admin portal are CDN-backed; "
            "API traffic flows through API Gateway to Lambda with secrets in Secrets Manager."
        ),
        "Amplify + API Gateway + Lambda + DynamoDB + SNS + CloudFront + Secrets Manager",
        (
            "Amplify hosts the mobile client bundle. API Gateway is the HTTP entry point. "
            "Lambda runs business logic. DynamoDB stores user state. SNS delivers push "
            "notifications. CloudFront caches media. Secrets Manager stores API keys."
        ),
        feature_flags={"file_upload": True, "ai": False, "background_processing": True},
        components=(
            _comp(
                "mobile",
                "Mobile Client Host",
                "mobile_app",
                "Cross-platform mobile shell and hosting",
                "Amplify",
                aws_service="Amplify",
                gcp_service="Firebase",
                order=0,
            ),
            _comp(
                "cdn",
                "Asset CDN",
                "cdn",
                "Cached images and static wellness content",
                "CDN",
                aws_service="CloudFront",
                gcp_service="Networking",
                order=1,
            ),
            _comp(
                "gateway",
                "API Gateway",
                "api_gateway",
                "Authenticated mobile API entry point",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=2,
            ),
            _comp(
                "api",
                "Wellness API",
                "service",
                "Check-ins, streaks, and recommendations",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=3,
            ),
            _comp(
                "database",
                "User State Store",
                "database",
                "Profiles, streaks, and exercise history",
                "Cosmos DB",
                aws_service="DynamoDB",
                gcp_service="Cloud Firestore",
                order=4,
            ),
            _comp(
                "notifications",
                "Push Notifications",
                "notification",
                "Daily reminders and milestone alerts",
                "Notification Hubs",
                aws_service="SNS",
                gcp_service="Firebase",
                order=5,
            ),
            _comp(
                "secrets",
                "App Secrets",
                "secrets",
                "Third-party API keys and signing secrets",
                "Key Vault",
                aws_service="Secrets Manager",
                gcp_service="Secret Manager",
                order=6,
            ),
        ),
    ),
    _scenario(
        "enterprise_web_platform",
        "Enterprise Web Platform",
        (
            "A production web SaaS with always-on ECS services behind an Application Load "
            "Balancer, relational data in RDS, Redis cache, full observability stack, "
            "and centralized secrets."
        ),
        "Amplify Hosting + ALB + ECS Fargate + RDS + ElastiCache + CloudWatch + Logs + X-Ray",
        (
            "Amplify Hosting serves the SPA. ALB distributes traffic to ECS Fargate tasks. "
            "RDS is the system of record. ElastiCache accelerates sessions. CloudWatch, Logs, "
            "and X-Ray provide metrics, logs, and distributed tracing."
        ),
        stage="production",
        feature_flags={"file_upload": False, "ai": False, "background_processing": False},
        components=(
            _comp(
                "web",
                "Web App Hosting",
                "web_app",
                "Customer-facing SPA hosting",
                "Amplify Hosting",
                aws_service="Amplify Hosting",
                gcp_service="Firebase Hosting",
                order=0,
            ),
            _comp(
                "load_balancer",
                "Load Balancer",
                "load_balancer",
                "Traffic distribution across ECS tasks",
                "Application Gateway",
                aws_service="Application Load Balancer",
                gcp_service="Networking",
                order=1,
            ),
            _comp(
                "api",
                "Core API Service",
                "service",
                "Business logic and REST APIs on Fargate",
                "Azure Container Apps",
                aws_service="ECS Fargate",
                gcp_service="Cloud Run",
                order=2,
            ),
            _comp(
                "database",
                "Primary Database",
                "database",
                "Relational tenant and user data",
                "SQL Database",
                aws_service="RDS",
                gcp_service="Cloud SQL",
                order=3,
            ),
            _comp(
                "cache",
                "Session Cache",
                "cache",
                "Hot session and catalog cache",
                "Redis Cache",
                aws_service="ElastiCache",
                gcp_service="Cloud Memorystore for Redis",
                order=4,
            ),
            _comp(
                "monitoring",
                "Metrics",
                "monitoring",
                "Service health and SLI metrics",
                "Azure Monitor",
                aws_service="CloudWatch",
                gcp_service="Cloud Monitoring",
                order=5,
            ),
            _comp(
                "logging",
                "Central Logs",
                "logging",
                "Application and infrastructure logs",
                "Log Analytics",
                aws_service="CloudWatch Logs",
                gcp_service="Cloud Logging",
                order=6,
            ),
            _comp(
                "tracing",
                "Distributed Tracing",
                "tracing",
                "Request traces across services",
                "Application Insights",
                aws_service="X-Ray",
                gcp_service="Cloud Trace",
                order=7,
            ),
            _comp(
                "secrets",
                "Platform Secrets",
                "secrets",
                "Database credentials and integration keys",
                "Key Vault",
                aws_service="Secrets Manager",
                gcp_service="Secret Manager",
                order=8,
            ),
        ),
    ),
    _scenario(
        "ai_analytics_suite",
        "AI Analytics Suite",
        (
            "An analytics product where users upload datasets, ask natural-language questions "
            "via Bedrock, run Athena SQL over S3 data lakes, and view QuickSight dashboards "
            "with operational metrics on CloudWatch Dashboards."
        ),
        "API Gateway + Lambda + Bedrock + S3 + Athena + QuickSight + CloudWatch Dashboards",
        (
            "API Gateway and Lambda orchestrate uploads and queries. Bedrock powers NL Q&A. "
            "S3 stores datasets. Athena scans data for reports. QuickSight renders BI views. "
            "CloudWatch Dashboards surfaces pipeline health."
        ),
        feature_flags={"file_upload": True, "ai": True, "background_processing": True},
        components=(
            _comp(
                "gateway",
                "Analytics API Gateway",
                "api_gateway",
                "Upload and query orchestration entry point",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=0,
            ),
            _comp(
                "api",
                "Query Orchestrator",
                "service",
                "Dataset ingestion and query coordination",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=1,
            ),
            _comp(
                "ai",
                "Generative AI",
                "ai_provider",
                "Natural-language analytics and summarization",
                "Foundry Models",
                aws_service="Bedrock",
                gcp_service="Vertex AI",
                order=2,
            ),
            _comp(
                "datalake",
                "Analytics Data Lake",
                "object_storage",
                "Raw and curated analytical datasets",
                "Blob Storage",
                aws_service="S3",
                gcp_service="Cloud Storage",
                order=3,
            ),
            _comp(
                "athena",
                "SQL Analytics",
                "analytics",
                "Ad-hoc SQL over S3 datasets",
                "Athena",
                aws_service="Athena",
                gcp_service="BigQuery",
                order=4,
            ),
            _comp(
                "quicksight",
                "BI Dashboards",
                "analytics",
                "Interactive reader dashboards for teams",
                "QuickSight",
                aws_service="QuickSight",
                gcp_service="Looker Studio",
                order=5,
            ),
            _comp(
                "ops_dashboards",
                "Ops Dashboards",
                "analytics",
                "Pipeline and ingestion operational views",
                "CloudWatch Dashboards",
                aws_service="CloudWatch Dashboards",
                gcp_service="Cloud Monitoring",
                order=6,
            ),
        ),
    ),
    _scenario(
        "marketplace_search_email",
        "Marketplace Search & Email",
        (
            "A B2B marketplace with full-text search, order queues, transactional email via "
            "SES, inventory alerts through CloudWatch Alarms, and runtime config in SSM."
        ),
        "CloudFront + API Gateway + Lambda + OpenSearch + RDS + SQS + SES + CloudWatch Alarms + SSM",
        (
            "CloudFront accelerates catalog assets. OpenSearch powers product search. "
            "RDS stores listings and orders. SQS decouples fulfillment. SES sends order "
            "emails. CloudWatch Alarms pages on inventory thresholds. SSM holds feature flags."
        ),
        feature_flags={"file_upload": True, "ai": False, "background_processing": True},
        components=(
            _comp(
                "cdn",
                "Catalog CDN",
                "cdn",
                "Product images and static catalog assets",
                "CDN",
                aws_service="CloudFront",
                gcp_service="Networking",
                order=0,
            ),
            _comp(
                "gateway",
                "Storefront Gateway",
                "api_gateway",
                "Public catalog and checkout APIs",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=1,
            ),
            _comp(
                "api",
                "Marketplace API",
                "service",
                "Listings, cart, and checkout logic",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=2,
            ),
            _comp(
                "search",
                "Product Search",
                "search",
                "Full-text search over listings",
                "Azure Cognitive Search",
                aws_service="OpenSearch Service",
                gcp_service="Vertex AI Search",
                order=3,
            ),
            _comp(
                "database",
                "Orders Database",
                "database",
                "Listings, orders, and seller accounts",
                "SQL Database",
                aws_service="RDS",
                gcp_service="Cloud SQL",
                order=4,
            ),
            _comp(
                "queue",
                "Fulfillment Queue",
                "queue",
                "Async order processing and webhooks",
                "Service Bus",
                aws_service="SQS",
                gcp_service="Cloud Pub/Sub",
                order=5,
            ),
            _comp(
                "email",
                "Transactional Email",
                "notification",
                "Order confirmations and shipping updates",
                "SES",
                aws_service="SES",
                gcp_service="SendGrid",
                order=6,
            ),
            _comp(
                "alerts",
                "Inventory Alerts",
                "alerting",
                "Low-stock and error-rate alarms",
                "CloudWatch Alarms",
                aws_service="CloudWatch Alarms",
                gcp_service="Cloud Monitoring",
                order=7,
            ),
            _comp(
                "config",
                "Runtime Config",
                "config",
                "Feature flags and integration parameters",
                "App Configuration",
                aws_service="SSM Parameter Store",
                gcp_service="Secret Manager",
                order=8,
            ),
        ),
    ),
    _scenario(
        "cloud_native_microservices",
        "Cloud-Native Microservices",
        (
            "An event-driven microservices stack with ALB-fronted ECS services, async workers, "
            "DynamoDB, AppConfig for deployments, and SNS alerting alongside CloudWatch observability."
        ),
        "ALB + ECS Fargate (API/worker) + DynamoDB + AppConfig + CloudWatch + CloudWatch Logs + SNS",
        (
            "ALB routes external traffic. ECS Fargate runs API and worker tasks. DynamoDB "
            "stores domain events. AppConfig manages safe rollouts. CloudWatch and Logs "
            "observe the fleet. SNS routes alert notifications."
        ),
        feature_flags={"file_upload": False, "ai": False, "background_processing": True},
        components=(
            _comp(
                "load_balancer",
                "Ingress Load Balancer",
                "load_balancer",
                "North-south traffic into the mesh",
                "Application Gateway",
                aws_service="Application Load Balancer",
                gcp_service="Networking",
                order=0,
            ),
            _comp(
                "api",
                "API Service",
                "service",
                "Synchronous command/query handlers",
                "Azure Container Apps",
                aws_service="ECS Fargate",
                gcp_service="Cloud Run",
                order=1,
            ),
            _comp(
                "worker",
                "Event Worker",
                "worker",
                "Async domain event processors",
                "Azure Container Apps",
                aws_service="ECS Fargate",
                gcp_service="Cloud Run",
                order=2,
            ),
            _comp(
                "database",
                "Event Store",
                "database",
                "DynamoDB tables for aggregates and outbox",
                "Cosmos DB",
                aws_service="DynamoDB",
                gcp_service="Cloud Firestore",
                order=3,
            ),
            _comp(
                "config",
                "Deployment Config",
                "config",
                "Gradual feature rollout and toggles",
                "App Configuration",
                aws_service="AppConfig",
                gcp_service="Cloud Firestore",
                order=4,
            ),
            _comp(
                "monitoring",
                "Fleet Metrics",
                "monitoring",
                "Autoscaling and error budgets",
                "Azure Monitor",
                aws_service="CloudWatch",
                gcp_service="Cloud Monitoring",
                order=5,
            ),
            _comp(
                "logging",
                "Structured Logs",
                "logging",
                "JSON logs from all tasks",
                "Log Analytics",
                aws_service="CloudWatch Logs",
                gcp_service="Cloud Logging",
                order=6,
            ),
            _comp(
                "alerting",
                "On-Call Alerts",
                "alerting",
                "SNS notifications for SLO breaches",
                "Azure Monitor",
                aws_service="SNS",
                gcp_service="Cloud Monitoring",
                order=7,
            ),
        ),
    ),
)

# Four additional AWS-native scenarios to reach twenty total benchmark products.
AWS_ADDITIONAL_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    _scenario(
        "serverless_photo_gallery",
        "Serverless Photo Gallery",
        (
            "A photo-sharing app where users upload images, browse albums, and share "
            "links. Static thumbnails are CDN-cached; metadata lives in DynamoDB with "
            "originals in S3. API traffic is bursty around uploads and gallery views."
        ),
        "CloudFront + API Gateway + Lambda + DynamoDB + S3",
        (
            "CloudFront serves thumbnails and static assets. API Gateway fronts REST "
            "endpoints. Lambda handles upload coordination and album APIs. DynamoDB "
            "stores album metadata. S3 holds full-resolution photos."
        ),
        feature_flags={"file_upload": True, "ai": False, "background_processing": False},
        components=(
            _comp(
                "cdn",
                "Thumbnail CDN",
                "cdn",
                "Cached thumbnails and static gallery assets",
                "CDN",
                aws_service="CloudFront",
                gcp_service="Networking",
                order=0,
            ),
            _comp(
                "gateway",
                "Gallery API Gateway",
                "api_gateway",
                "Authenticated upload and album APIs",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=1,
            ),
            _comp(
                "api",
                "Gallery API",
                "service",
                "Upload coordination, albums, and sharing links",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=2,
            ),
            _comp(
                "database",
                "Album Metadata",
                "database",
                "Albums, tags, and sharing permissions",
                "Cosmos DB",
                aws_service="DynamoDB",
                gcp_service="Cloud Firestore",
                order=3,
            ),
            _comp(
                "files",
                "Photo Storage",
                "object_storage",
                "Full-resolution user photo originals",
                "Blob Storage",
                aws_service="S3",
                gcp_service="Cloud Storage",
                order=4,
            ),
        ),
    ),
    _scenario(
        "newsletter_platform",
        "Newsletter & Email Platform",
        (
            "A newsletter SaaS where creators manage subscriber lists, compose campaigns, "
            "and send bulk email. SQS queues campaign batches; Lambda processes sends via "
            "SES. Subscriber profiles and campaign stats live in RDS."
        ),
        "API Gateway + Lambda + RDS + SQS + SES + Secrets Manager",
        (
            "API Gateway exposes creator APIs. Lambda orchestrates list management and "
            "send jobs. RDS stores subscribers and campaigns. SQS buffers bulk sends. "
            "SES delivers email. Secrets Manager holds SMTP and API credentials."
        ),
        feature_flags={"file_upload": False, "ai": False, "background_processing": True},
        components=(
            _comp(
                "gateway",
                "Campaign API Gateway",
                "api_gateway",
                "Creator dashboard and campaign APIs",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=0,
            ),
            _comp(
                "api",
                "Campaign API",
                "service",
                "List management, templates, and send orchestration",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=1,
            ),
            _comp(
                "database",
                "Subscriber Database",
                "database",
                "Subscribers, lists, and campaign history",
                "SQL Database",
                aws_service="RDS",
                gcp_service="Cloud SQL",
                order=2,
            ),
            _comp(
                "queue",
                "Send Queue",
                "queue",
                "Bulk campaign send job buffering",
                "Service Bus",
                aws_service="SQS",
                gcp_service="Cloud Pub/Sub",
                order=3,
            ),
            _comp(
                "email",
                "Bulk Email",
                "notification",
                "Campaign and transactional email delivery",
                "SES",
                aws_service="SES",
                gcp_service="SendGrid",
                order=4,
            ),
            _comp(
                "secrets",
                "Integration Secrets",
                "secrets",
                "Email provider keys and webhook signing secrets",
                "Key Vault",
                aws_service="Secrets Manager",
                gcp_service="Secret Manager",
                order=5,
            ),
        ),
    ),
    _scenario(
        "realtime_leaderboard",
        "Real-Time Leaderboard Game",
        (
            "A mobile game backend with live leaderboards, score submissions, and push "
            "notifications for rank changes. DynamoDB holds scores; Lambda validates "
            "submissions; SNS notifies players; API Gateway handles game client traffic."
        ),
        "API Gateway + Lambda + DynamoDB + SNS + CloudWatch",
        (
            "API Gateway is the game client entry point. Lambda validates scores and "
            "updates ranks. DynamoDB stores leaderboard entries with low-latency reads. "
            "SNS sends rank-change push notifications. CloudWatch tracks API latency."
        ),
        feature_flags={"file_upload": False, "ai": False, "background_processing": True},
        components=(
            _comp(
                "gateway",
                "Game API Gateway",
                "api_gateway",
                "Mobile game client REST endpoints",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=0,
            ),
            _comp(
                "api",
                "Score API",
                "service",
                "Score validation and leaderboard updates",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=1,
            ),
            _comp(
                "database",
                "Leaderboard Store",
                "database",
                "Player scores, ranks, and session tokens",
                "Cosmos DB",
                aws_service="DynamoDB",
                gcp_service="Cloud Firestore",
                order=2,
            ),
            _comp(
                "notifications",
                "Rank Alerts",
                "notification",
                "Push notifications for rank changes and milestones",
                "Notification Hubs",
                aws_service="SNS",
                gcp_service="Firebase",
                order=3,
            ),
            _comp(
                "monitoring",
                "Game Metrics",
                "monitoring",
                "API latency, error rates, and active sessions",
                "Azure Monitor",
                aws_service="CloudWatch",
                gcp_service="Cloud Monitoring",
                order=4,
            ),
        ),
    ),
    _scenario(
        "secure_document_vault",
        "Secure Document Vault",
        (
            "An enterprise document vault where users upload confidential files, "
            "control access permissions, and audit downloads. Files are encrypted in S3; "
            "metadata and ACLs live in RDS; Secrets Manager rotates encryption keys; "
            "CloudWatch Logs captures audit trails."
        ),
        "API Gateway + Lambda + RDS + S3 + Secrets Manager + CloudWatch Logs",
        (
            "API Gateway provides authenticated document APIs. Lambda enforces ACL checks "
            "and presigned URLs. RDS stores document metadata and permissions. S3 stores "
            "encrypted file content. Secrets Manager holds encryption keys. CloudWatch "
            "Logs records audit events."
        ),
        stage="production",
        feature_flags={"file_upload": True, "ai": False, "background_processing": False},
        components=(
            _comp(
                "gateway",
                "Vault API Gateway",
                "api_gateway",
                "Authenticated document upload and download APIs",
                "API Management",
                aws_service="API Gateway",
                gcp_service="API Gateway",
                order=0,
            ),
            _comp(
                "api",
                "Document API",
                "service",
                "ACL enforcement, presigned URLs, and search",
                "Functions",
                aws_service="Lambda",
                gcp_service="Cloud Run Functions",
                order=1,
            ),
            _comp(
                "database",
                "Document Index",
                "database",
                "Document metadata, permissions, and audit index",
                "SQL Database",
                aws_service="RDS",
                gcp_service="Cloud SQL",
                order=2,
            ),
            _comp(
                "files",
                "Encrypted File Storage",
                "object_storage",
                "Encrypted document blobs and versions",
                "Blob Storage",
                aws_service="S3",
                gcp_service="Cloud Storage",
                order=3,
            ),
            _comp(
                "secrets",
                "Encryption Keys",
                "secrets",
                "Document encryption keys and rotation secrets",
                "Key Vault",
                aws_service="Secrets Manager",
                gcp_service="Secret Manager",
                order=4,
            ),
            _comp(
                "logging",
                "Audit Logs",
                "logging",
                "Download and permission-change audit trail",
                "Log Analytics",
                aws_service="CloudWatch Logs",
                gcp_service="Cloud Logging",
                order=5,
            ),
        ),
    ),
)

# Twenty AWS benchmark scenarios: core apps, platform/observability stacks, and extras.
AWS_TWENTY_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    *ALL_BENCHMARK_SCENARIOS,
    *AWS_PLATFORM_BENCHMARK_SCENARIOS,
    *AWS_ADDITIONAL_SCENARIOS,
)


def twenty_scenario_components(scenario: BenchmarkScenario) -> list:
    """Return MappedComponent list for any scenario in AWS_TWENTY_SCENARIOS."""
    return _mapped_components(scenario.components)


# Services introduced in the extended AWS pricing implementation (for test assertions).
AWS_EXTENDED_SERVICES: frozenset[str] = frozenset(
    {
        "Amplify",
        "Amplify Hosting",
        "Bedrock",
        "ElastiCache",
        "OpenSearch Service",
        "Athena",
        "QuickSight",
        "SES",
        "CloudWatch",
        "CloudWatch Logs",
        "CloudWatch Dashboards",
        "CloudWatch Alarms",
        "SSM Parameter Store",
        "AppConfig",
        "X-Ray",
    }
)


def platform_scenario_components(scenario: BenchmarkScenario) -> list:
    """Return MappedComponent list for one AWS platform scenario."""
    return _mapped_components(scenario.components)
