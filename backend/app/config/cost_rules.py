"""Rule-based pricing tables for cloud infrastructure cost estimation."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Usage band numeric values
# ---------------------------------------------------------------------------

USER_SCALE_FACTOR: dict[str, float] = {
    "100": 1.0,
    "1000": 1.6,
    "10000": 3.5,
    "100000+": 8.0,
}

ESTIMATED_MONTHLY_USERS: dict[str, int] = {
    "100": 100,
    "1000": 1_000,
    "10000": 10_000,
    "100000+": 100_000,
}

FILES_PER_MONTH_MIDPOINT: dict[str, int] = {
    "under_1k": 500,
    "1k_10k": 5_000,
    "10k_plus": 25_000,
}

AVG_FILE_SIZE_MB: dict[str, float] = {
    "small": 0.5,
    "medium": 5.0,
    "large": 25.0,
}

# Rough API requests per user per month (drives API gateway + CDN scaling)
API_REQUESTS_PER_USER_MONTH: tuple[float, float] = (50.0, 200.0)

STAGE_CLOUD_OVERHEAD: dict[str, tuple[float, float]] = {
    "mvp": (4.0, 10.0),
    "production": (10.0, 25.0),
}

STAGE_COMPUTE_MULTIPLIER: dict[str, float] = {
    "mvp": 1.0,
    "production": 1.35,
}

STAGE_DATABASE_MULTIPLIER: dict[str, float] = {
    "mvp": 1.0,
    "production": 1.4,
}

STAGE_OBSERVABILITY_MULTIPLIER: dict[str, float] = {
    "mvp": 1.0,
    "production": 1.5,
}

# Relative provider pricing (low, high multipliers vs baseline)
PROVIDER_COST_MULTIPLIER: dict[str, tuple[float, float]] = {
    "aws": (1.0, 1.0),
    "gcp": (0.9, 0.94),
    "azure": (1.06, 1.1),
}

# Ordered infrastructure categories shown in the UI
INFRASTRUCTURE_CATEGORY_ORDER: tuple[str, ...] = (
    "compute",
    "database",
    "storage",
    "api_gateway",
    "load_balancer",
    "cdn",
    "queue",
    "cache",
    "search",
    "monitoring",
    "logging",
    "tracing",
    "alerting",
    "secrets",
    "backups",
)

INFRASTRUCTURE_CATEGORY_LABELS: dict[str, str] = {
    "compute": "Compute",
    "database": "Database",
    "storage": "Object storage",
    "api_gateway": "API gateway",
    "load_balancer": "Load balancer",
    "cdn": "CDN",
    "queue": "Queue",
    "cache": "Cache",
    "search": "Search",
    "monitoring": "Monitoring",
    "logging": "Logging",
    "tracing": "Tracing",
    "alerting": "Alerting",
    "secrets": "Secrets",
    "backups": "Backups",
}

# Component type → infrastructure category (fallback when services are mapped)
COMPONENT_TYPE_TO_INFRA_CATEGORY: dict[str, str] = {
    "service": "compute",
    "worker": "compute",
    "database": "database",
    "object_storage": "storage",
    "api_gateway": "api_gateway",
    "api": "api_gateway",
    "load_balancer": "load_balancer",
    "cdn": "cdn",
    "queue": "queue",
    "cache": "cache",
    "search": "search",
    "monitoring": "monitoring",
    "logging": "logging",
    "tracing": "tracing",
    "alerting": "alerting",
    "secrets": "secrets",
    "backup": "backups",
    "web_app": "cdn",
    "admin_panel": "cdn",
}

# Service keyword classification (first matching category wins per service)
INFRASTRUCTURE_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("api_gateway", ("api gateway", "api management", "apigateway")),
    ("load_balancer", ("load balancer", "application gateway", "cloud load balancing")),
    ("storage", ("s3", "blob storage", "cloud storage", "object storage")),
    ("database", (
        "rds", "dynamodb", "cloud sql", "firestore", "cosmos", "aurora",
        "postgres", "mysql", "sql database", "bigtable", "spanner",
    )),
    ("queue", ("sqs", "pub/sub", "service bus", "cloud tasks", "queue storage", "eventbridge")),
    ("cache", ("elasticache", "memorystore", "cache for redis", "redis")),
    ("search", ("opensearch", "vertex ai search", "ai search", "elasticsearch")),
    ("cdn", ("cloudfront", "cloud cdn", "azure cdn", "cdn")),
    ("monitoring", ("cloudwatch", "cloud monitoring", "azure monitor", "application insights")),
    ("logging", ("cloudwatch logs", "cloud logging", "log analytics", "logging")),
    ("tracing", ("x-ray", "cloud trace", "application insights")),
    ("alerting", ("alarms", "alert", "action groups", "monitoring alerts")),
    ("secrets", ("secrets manager", "secret manager", "key vault", "parameter store")),
    ("backups", ("aws backup", "backup and dr", "azure backup", "recovery services", "versioning")),
    ("compute", (
        "lambda", "cloud run", "cloud functions", "azure functions",
        "fargate", "ecs", "container apps", "app service", "elastic beanstalk",
    )),
)

# Base monthly USD ranges per category before scaling
INFRASTRUCTURE_CATEGORY_BASE: dict[str, tuple[float, float]] = {
    "compute": (12.0, 40.0),
    "database": (15.0, 55.0),
    "storage": (2.0, 6.0),
    "api_gateway": (5.0, 22.0),
    "load_balancer": (8.0, 28.0),
    "cdn": (4.0, 20.0),
    "queue": (3.0, 16.0),
    "cache": (10.0, 38.0),
    "search": (18.0, 70.0),
    "monitoring": (4.0, 18.0),
    "logging": (3.0, 15.0),
    "tracing": (2.0, 12.0),
    "alerting": (2.0, 10.0),
    "secrets": (1.0, 6.0),
    "backups": (3.0, 14.0),
}

INFRASTRUCTURE_USER_EXPONENT: dict[str, float] = {
    "compute": 0.55,
    "database": 0.48,
    "storage": 0.0,
    "api_gateway": 0.42,
    "load_balancer": 0.38,
    "cdn": 0.35,
    "queue": 0.38,
    "cache": 0.32,
    "search": 0.28,
    "monitoring": 0.25,
    "logging": 0.22,
    "tracing": 0.2,
    "alerting": 0.18,
    "secrets": 0.1,
    "backups": 0.15,
}

# Object storage $/GB-month by provider
STORAGE_COST_PER_GB_BY_PROVIDER: dict[str, tuple[float, float]] = {
    "aws": (0.023, 0.055),
    "gcp": (0.020, 0.050),
    "azure": (0.018, 0.048),
}

# API gateway: cost per million requests
API_GATEWAY_COST_PER_MILLION: dict[str, tuple[float, float]] = {
    "aws": (3.5, 5.0),
    "gcp": (3.0, 4.5),
    "azure": (3.8, 5.5),
}

FILE_PROCESSING_COMPUTE_SURCHARGE: tuple[float, float] = (5.0, 22.0)
REALTIME_COMPUTE_SURCHARGE: tuple[float, float] = (8.0, 35.0)
DASHBOARDS_DATABASE_SURCHARGE: tuple[float, float] = (4.0, 18.0)

# Exclude AI API services from infrastructure classification
AI_CLOUD_EXCLUDED_KEYWORDS: tuple[str, ...] = (
    "openai",
    "azure openai",
    "bedrock",
    "gemini",
    "vertex ai",
    "claude",
    "anthropic",
)

# Rough non-infrastructure estimates (unchanged, low priority)
STAGE_EXTERNAL_OVERHEAD: dict[str, float] = {"mvp": 1.0, "production": 1.15}
ROUGH_AI_MONTHLY: tuple[float, float] = (25.0, 150.0)
ROUGH_EXTERNAL_MONTHLY: tuple[float, float] = (10.0, 75.0)

# Metadata labels
EXPECTED_USERS_ASSUMPTION_LABELS: dict[str, str] = {
    "100": "Up to 100 users",
    "1000": "Up to 1,000 users",
    "10000": "Up to 10,000 users",
    "100000+": "100,000+ users",
}

FILES_PER_MONTH_LABELS: dict[str, str] = {
    "under_1k": "Under 1K files per month",
    "1k_10k": "1K–10K files per month",
    "10k_plus": "10K+ files per month",
}

AVG_FILE_SIZE_LABELS: dict[str, str] = {
    "small": "small",
    "medium": "medium",
    "large": "large",
}

AI_REQUESTS_LABELS: dict[str, str] = {
    "under_100": "Under 100 per day",
    "100_1k": "100–1K per day",
    "1k_10k": "1K–10K per day",
    "10k_plus": "10K+ per day",
}

AI_TYPE_LABELS: dict[str, str] = {
    "chat": "Chat",
    "document_processing": "Document processing",
    "recommendations": "Recommendations",
    "search": "Search",
    "image_generation": "Image generation",
    "audio_processing": "Audio processing",
}

REALTIME_TYPE_LABELS: dict[str, str] = {
    "live_chat": "Live chat",
    "live_dashboard": "Live dashboard",
    "collaboration": "Collaboration",
}

COST_ESTIMATION_DISCLAIMER = (
    "Cloud infrastructure estimates are rule-based monthly ranges for AWS, GCP, and Azure. "
    "AI, payment, notification, and third-party API costs are rough placeholders only. "
    "Actual costs vary by region, traffic, provider pricing, and service configuration."
)
