"""Application-wide constants and default values (non-secret configuration)."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Validation limits
# ---------------------------------------------------------------------------

DESCRIPTION_MAX_CHARS = 1200
TOKEN_CHARS_PER_TOKEN = 4
COMPONENT_KEY_MAX_LENGTH = 60
SLUG_MAX_LENGTH = 60

# ---------------------------------------------------------------------------
# Project catalog
# ---------------------------------------------------------------------------

PROJECT_TYPES: list[dict[str, str]] = [
    {
        "type": "web_app",
        "label": "Web App",
        "description": "Browser-based application accessed over the web.",
    },
    {
        "type": "mobile_app",
        "label": "Mobile App",
        "description": "Native or cross-platform app installed on a device.",
    },
    {
        "type": "chrome_extension",
        "label": "Chrome Extension",
        "description": "Browser extension running inside Chrome.",
    },
]

STAGE_LABELS: dict[str, str] = {"mvp": "MVP", "production": "Production"}

PLATFORM_LABELS: dict[str, str] = {"web": "Web", "mobile": "Mobile"}

# ---------------------------------------------------------------------------
# Firestore collections (the only application database)
# ---------------------------------------------------------------------------

FIRESTORE_PROJECTS_COLLECTION = "projects"
FIRESTORE_USERS_COLLECTION = "users"
FIRESTORE_ARCHITECTURE_CATEGORIES_COLLECTION = "architecture_categories"
FIRESTORE_CLOUD_SERVICE_MAPPINGS_COLLECTION = "cloud_service_mappings"
FIRESTORE_PRICING_SERVICES_COLLECTION = "pricing_services"
# Sub-collection under a project document holding architecture component selections.
FIRESTORE_ARCHITECTURE_SELECTIONS_SUBCOLLECTION = "architecture_selections"
# Sub-collection under a project document holding global usage model runs.
FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION = "global_usage_models"
# Sub-collection under a project document holding pricing runs (Step 4).
FIRESTORE_PRICING_RUNS_SUBCOLLECTION = "pricing_runs"
# Sub-collection under a pricing run holding per-provider results.
FIRESTORE_PROVIDER_PRICING_SUBCOLLECTION = "provider_results"

PROJECT_TYPE_LABELS: dict[str, str] = {
    item["type"]: item["label"] for item in PROJECT_TYPES
}

EXPECTED_USERS_LABELS: dict[str, str] = {
    "100": "Up to 100",
    "1000": "Up to 1,000",
    "10000": "Up to 10,000",
    "100000+": "100,000+",
}

REQUIREMENT_LABELS: dict[str, str] = {
    "auth": "Authentication",
    "file_upload": "File uploads",
    "background_processing": "Background processing",
    "dashboards": "Dashboards / reports",
    "ai": "AI usage",
    "payments": "Payments",
    "include_edge_cases": "Edge cases (rate limiting, backups, third-party outages)",
}

REQUIREMENT_KEYS: tuple[str, ...] = tuple(REQUIREMENT_LABELS.keys())

# Step 1 intake cards (frontend ``requirementsConfig.js``). Used only for human-readable
# prompt text — these keys are NOT architecture category ids.
INTAKE_REQUIREMENT_LABELS: dict[str, str] = {
    "authentication": "Authentication",
    "file_uploads": "File uploads",
    "background_processing": "Background processing",
    "dashboards_reports": "Dashboards and reports",
    "ai_usage": "AI usage",
    "payments": "Payments",
    "external_integrations": "External integrations",
    "realtime": "Real-time features",
    "reliability": "Reliability",
    "notifications": "Notifications",
}

# ---------------------------------------------------------------------------
# Component types
# ---------------------------------------------------------------------------

MAIN_ARCHITECTURE_COMPONENT_TYPES: frozenset[str] = frozenset(
    {
        "user",
        "web_app",
        "mobile_app",
        "admin_panel",
        "cdn",
        "load_balancer",
        "api_gateway",
        "service",
        "worker",
        "database",
        "cache",
        "queue",
        "object_storage",
        "search",
        "external_api",
        "ai_provider",
        "payment",
        "notification",
        "analytics",
    }
)

SUPPORTING_INFRASTRUCTURE_COMPONENT_TYPES: frozenset[str] = frozenset(
    {
        "secrets",
        "config",
        "monitoring",
        "logging",
        "tracing",
        "alerting",
    }
)

# Legacy aliases and project-specific types kept for backward compatibility.
LEGACY_COMPONENT_TYPES: frozenset[str] = frozenset(
    {
        "browser_extension",
        "api",
        "authentication",
        "auth",
        "ai_service",
        "integration",
        "backup",
    }
)

VALID_COMPONENT_TYPES: frozenset[str] = (
    MAIN_ARCHITECTURE_COMPONENT_TYPES
    | SUPPORTING_INFRASTRUCTURE_COMPONENT_TYPES
    | LEGACY_COMPONENT_TYPES
)

COMPONENT_TYPE_ALIASES: dict[str, str] = {
    "api": "api_gateway",
    "authentication": "auth",
    "ai_service": "ai_provider",
    "integration": "external_api",
}

DEFAULT_COMPONENT_TYPE = "api_gateway"
VALID_COMPONENT_TAGS: frozenset[str] = frozenset({"required", "optional"})

COMPONENT_TYPE_KEY_MAP: dict[str, str] = {
    "user": "user",
    "web_app": "client_web",
    "mobile_app": "client_mobile",
    "admin_panel": "admin_panel",
    "browser_extension": "client_extension",
    "cdn": "cdn",
    "load_balancer": "load_balancer",
    "api": "api_layer",
    "api_gateway": "api_layer",
    "service": "app_service",
    "authentication": "auth",
    "auth": "auth",
    "database": "database",
    "object_storage": "object_storage",
    "queue": "queue_worker",
    "worker": "queue_worker",
    "cache": "cache",
    "search": "search",
    "ai_service": "ai_service",
    "ai_provider": "ai_service",
    "monitoring": "monitoring",
    "logging": "logging",
    "tracing": "tracing",
    "alerting": "alerting",
    "secrets": "secrets",
    "config": "config",
    "analytics": "analytics",
    "notification": "push_notifications",
    "payment": "payments",
    "external_api": "integrations",
    "integration": "integrations",
    "backup": "backup",
}

COMPONENT_KEY_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("client_web", ("web client", "web app", "frontend", "browser")),
    ("client_mobile", ("mobile app", "mobile client", "ios", "android")),
    ("client_extension", ("chrome extension", "browser extension", "extension")),
    ("api_layer", ("api gateway", "api layer", "rest api", "graphql")),
    ("app_service", ("application service", "backend service", "app server", "business logic")),
    ("database", ("database", "data store", "postgres", "mysql", "sql")),
    ("cdn", ("cdn", "content delivery", "caching layer", "cache")),
    ("auth", ("authentication", "auth", "identity", "login", "sso")),
    ("object_storage", ("object storage", "file storage", "blob storage", "s3")),
    ("queue_worker", ("queue", "worker", "background job", "async processing", "job queue")),
    ("analytics", ("analytics", "reporting", "dashboard", "business intelligence")),
    ("ai_service", ("ai service", "machine learning", "llm", "openai", "inference")),
    ("payments", ("payment", "billing", "stripe", "checkout")),
    ("push_notifications", ("push notification", "notification service", "fcm")),
    ("monitoring", ("monitoring", "observability", "metrics")),
    ("logging", ("logging", "log aggregation")),
    ("backup", ("backup", "disaster recovery")),
    ("alerts", ("alert", "alerting", "on-call")),
    ("security", ("security", "waf", "firewall", "encryption")),
]

FEATURE_FLAG_KEYS: tuple[str, ...] = ("file_upload", "ai", "background_processing")

# ---------------------------------------------------------------------------
# Diagram types
# ---------------------------------------------------------------------------

DIAGRAM_KEYS: tuple[str, ...] = ("high_level", "system_flow", "technical_architecture")

LEGACY_DIAGRAM_KEY_ALIASES: dict[str, str] = {
    "production_architecture": "technical_architecture",
}

DEFAULT_DIAGRAM_TITLES: dict[str, str] = {
    "high_level": "High Level Design",
    "system_flow": "System Flow",
    "technical_architecture": "Technical Architecture",
}

DIAGRAM_EXCLUDED_TYPES: dict[str, frozenset[str]] = {
    "high_level": SUPPORTING_INFRASTRUCTURE_COMPONENT_TYPES,
    "system_flow": SUPPORTING_INFRASTRUCTURE_COMPONENT_TYPES,
}

VALID_DIAGRAM_GROUPS: frozenset[str] = frozenset(
    {"experience", "platform", "data", "operations"}
)

AI_RESPONSE_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "components",
    "architecture",
    "diagrams",
)

COMPONENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "name",
    "type",
    "tag",
    "reason",
    "implementation_options",
)
VALID_IMPLEMENTATION_MODELS: frozenset[str] = frozenset(
    {"serverless", "container", "managed_service", "external_provider"}
)

IMPLEMENTATION_MODEL_LABELS: dict[str, str] = {
    "serverless": "Serverless",
    "container": "Container / Server",
    "managed_service": "Managed Service",
    "external_provider": "External Provider",
}

# ---------------------------------------------------------------------------
# Cloud providers
# ---------------------------------------------------------------------------

CLOUD_PROVIDERS: tuple[str, ...] = ("aws", "gcp", "azure")

# Sequential order for Step 4 progressive pricing (AWS → Azure → GCP).
PRICING_GENERATION_ORDER: tuple[str, ...] = ("aws", "azure", "gcp")

CLOUD_PROVIDER_LABELS: dict[str, str] = {
    "aws": "AWS",
    "gcp": "Google Cloud",
    "azure": "Azure",
}

# Status labels shown in the UI while each provider is calculating.
PRICING_STATUS_LABELS: dict[str, str] = {
    "aws": "Calculating AWS pricing...",
    "azure": "Calculating Azure pricing...",
    "gcp": "Calculating Google Cloud pricing...",
}

PRICING_SERVICE_DISPLAY_NAMES: dict[str, str] = {
    "aws_lambda": "AWS Lambda",
    "aws_s3": "Amazon S3",
    "aws_ec2": "Amazon EC2",
    "aws_rds": "Amazon RDS",
    "aws_api_gateway": "Amazon API Gateway",
    "aws_sqs": "Amazon SQS",
    "aws_dynamodb": "Amazon DynamoDB",
    "aws_elasticache_redis": "Amazon ElastiCache for Redis",
    "aws_elasticache_memcached": "Amazon ElastiCache for Memcached",
    "gcp_cloud_run": "Google Cloud Run",
    "gcp_cloud_functions": "Google Cloud Functions",
    "gcp_cloud_storage": "Google Cloud Storage",
    "gcp_cloud_sql": "Google Cloud SQL",
    "gcp_firestore": "Google Cloud Firestore",
    "gcp_api_gateway": "Google Cloud API Gateway",
    "azure_functions": "Azure Functions",
    "azure_blob_storage": "Azure Blob Storage",
    "azure_sql_database": "Azure SQL Database",
    "azure_cosmos_db": "Azure Cosmos DB",
    "azure_api_management": "Azure API Management",
    "azure_queue_storage": "Azure Queue Storage",
    "azure_cache_for_redis": "Azure Cache for Redis",
}

CLOUD_PROVIDER_ALIASES: dict[str, tuple[str, ...]] = {
    "aws": ("aws", "amazon", "amazon web services"),
    "gcp": ("gcp", "google", "google cloud", "google cloud platform"),
    "azure": ("azure", "microsoft azure"),
}


def _cloud_defaults(
    *,
    aws: list[str],
    gcp: list[str],
    azure: list[str],
) -> dict[str, list[str]]:
    return {"aws": list(aws), "gcp": list(gcp), "azure": list(azure)}


def _uniform_cloud_defaults(*options: str) -> dict[str, list[str]]:
    return {provider: list(options) for provider in CLOUD_PROVIDERS}


_HOSTING_DEFAULTS = _cloud_defaults(
    aws=["Amplify Hosting"],
    gcp=["Firebase Hosting"],
    azure=["Azure Static Web Apps"],
)
_API_GATEWAY_DEFAULTS = _cloud_defaults(
    aws=["API Gateway"],
    gcp=["API Gateway"],
    azure=["API Management"],
)
_AUTH_DEFAULTS = _cloud_defaults(
    aws=["Cognito"],
    gcp=["Firebase Authentication", "Identity Platform"],
    azure=["Entra ID B2C"],
)
_AI_DEFAULTS = _cloud_defaults(
    aws=["Bedrock"],
    gcp=["Gemini API", "Vertex AI"],
    azure=["Azure OpenAI Service"],
)

CLOUD_DEFAULTS_BY_TYPE: dict[str, dict[str, list[str]]] = {
    "user": _uniform_cloud_defaults("N/A"),
    "web_app": _HOSTING_DEFAULTS,
    "admin_panel": _HOSTING_DEFAULTS,
    "mobile_app": _cloud_defaults(
        aws=["Amplify"],
        gcp=["Firebase"],
        azure=["Azure App Center"],
    ),
    "browser_extension": _HOSTING_DEFAULTS,
    "cdn": _cloud_defaults(
        aws=["CloudFront"],
        gcp=["Cloud CDN"],
        azure=["Azure CDN"],
    ),
    "api_gateway": _API_GATEWAY_DEFAULTS,
    "api": _API_GATEWAY_DEFAULTS,
    "load_balancer": _cloud_defaults(
        aws=["Application Load Balancer"],
        gcp=["Cloud Load Balancing"],
        azure=["Application Gateway"],
    ),
    "service": _cloud_defaults(
        aws=["Lambda", "ECS Fargate"],
        gcp=["Cloud Run", "Cloud Functions"],
        azure=["Azure Functions", "Container Apps"],
    ),
    "worker": _cloud_defaults(
        aws=["Lambda", "ECS Fargate"],
        gcp=["Cloud Run Jobs", "Cloud Functions"],
        azure=["Azure Functions", "Container Apps Jobs"],
    ),
    "database": _cloud_defaults(
        aws=["DynamoDB", "RDS"],
        gcp=["Firestore", "Cloud SQL"],
        azure=["Cosmos DB", "Azure SQL Database"],
    ),
    "object_storage": _cloud_defaults(
        aws=["S3"],
        gcp=["Cloud Storage"],
        azure=["Blob Storage"],
    ),
    "queue": _cloud_defaults(
        aws=["SQS"],
        gcp=["Pub/Sub", "Cloud Tasks"],
        azure=["Service Bus", "Queue Storage"],
    ),
    "cache": _cloud_defaults(
        aws=["ElastiCache"],
        gcp=["Memorystore"],
        azure=["Azure Cache for Redis"],
    ),
    "search": _cloud_defaults(
        aws=["OpenSearch Service"],
        gcp=["Vertex AI Search"],
        azure=["Azure AI Search"],
    ),
    "authentication": _AUTH_DEFAULTS,
    "auth": _AUTH_DEFAULTS,
    "secrets": _cloud_defaults(
        aws=["Secrets Manager", "SSM Parameter Store"],
        gcp=["Secret Manager"],
        azure=["Key Vault"],
    ),
    "config": _cloud_defaults(
        aws=["AppConfig", "SSM Parameter Store"],
        gcp=["Secret Manager", "Firestore"],
        azure=["App Configuration"],
    ),
    "monitoring": _cloud_defaults(
        aws=["CloudWatch"],
        gcp=["Cloud Monitoring"],
        azure=["Azure Monitor"],
    ),
    "logging": _cloud_defaults(
        aws=["CloudWatch Logs"],
        gcp=["Cloud Logging"],
        azure=["Azure Monitor Logs", "Log Analytics"],
    ),
    "tracing": _cloud_defaults(
        aws=["X-Ray"],
        gcp=["Cloud Trace"],
        azure=["Application Insights"],
    ),
    "alerting": _cloud_defaults(
        aws=["CloudWatch Alarms", "SNS"],
        gcp=["Cloud Monitoring Alerts"],
        azure=["Azure Monitor Alerts", "Action Groups"],
    ),
    "analytics": _cloud_defaults(
        aws=["CloudWatch Dashboards", "Athena", "QuickSight"],
        gcp=["Looker Studio", "BigQuery"],
        azure=["Application Insights", "Power BI"],
    ),
    "notification": _cloud_defaults(
        aws=["SNS", "SES"],
        gcp=["Firebase Cloud Messaging", "SendGrid"],
        azure=["Notification Hubs", "Communication Services"],
    ),
    "payment": _uniform_cloud_defaults("Stripe", "Paddle"),
    "external_api": _uniform_cloud_defaults("Third-party API"),
    "integration": _cloud_defaults(
        aws=["EventBridge", "API Gateway"],
        gcp=["Pub/Sub", "Workflows"],
        azure=["Logic Apps", "Service Bus"],
    ),
    "ai_provider": _AI_DEFAULTS,
    "ai_service": _AI_DEFAULTS,
    "backup": _cloud_defaults(
        aws=["AWS Backup", "S3 Versioning"],
        gcp=["Backup and DR", "Cloud Storage Versioning"],
        azure=["Azure Backup", "Recovery Services Vault"],
    ),
}

CLOUD_DEFAULTS_FALLBACK_TYPE = "api_gateway"

# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

COST_CURRENCY = "USD"

COST_BASELINE: dict[str, tuple[float, float]] = {
    "aws": (15, 45),
    "gcp": (12, 40),
    "azure": (18, 50),
}

COST_FEATURE_BANDS: dict[str, dict[str, tuple[float, float]]] = {
    "file_upload": {"aws": (5, 20), "gcp": (4, 18), "azure": (5, 22)},
    "ai": {"aws": (20, 120), "gcp": (18, 110), "azure": (22, 130)},
    "background_processing": {"aws": (8, 30), "gcp": (7, 28), "azure": (9, 32)},
}

COST_PRODUCTION_BAND: dict[str, tuple[float, float]] = {
    "aws": (15, 60),
    "gcp": (12, 55),
    "azure": (16, 65),
}

COST_USER_MULTIPLIER: dict[str, float] = {
    "100": 1.0,
    "1000": 1.8,
    "10000": 4.0,
    "100000+": 9.0,
}

STAGE_PRODUCTION = "production"

# ---------------------------------------------------------------------------
# Object storage (AI generation artifacts)
# ---------------------------------------------------------------------------

STORAGE_PROVIDERS: tuple[str, ...] = ("local", "gcs", "s3")

GENERATION_STORAGE_PREFIX = "generations"
GENERATION_REQUEST_FILENAME = "request.json"
GENERATION_RESPONSE_FILENAME = "response.json"

GENERATION_TYPE_ARCHITECTURE = "architecture"

# ---------------------------------------------------------------------------
# AI generation
# ---------------------------------------------------------------------------

AI_RESPONSE_FORMAT = {"type": "json_object"}
AI_TEMPERATURE = 0.2
OPENAI_REQUEST_TIMEOUT_SECONDS = 300
OPENAI_MAX_OUTPUT_TOKENS = 8000

AI_SYSTEM_PROMPT = (
    "You are a senior software architect. Design cost-effective, high-level cloud architectures "
    "matched to the requested stage and requirements. Return only valid JSON."
)

PROMPT_COMPONENT_TYPE_LIST = (
    "user, web_app, mobile_app, admin_panel, cdn, load_balancer, api_gateway, "
    "service, worker, database, cache, queue, object_storage, search, "
    "external_api, ai_provider, payment, notification, analytics, "
    "secrets, config, monitoring, logging, tracing, alerting"
)

PROMPT_STAGE_GUIDANCE_MVP = """For MVP:
- Prefer simple, managed, and serverless services.
- Avoid over-engineering."""

PROMPT_STAGE_GUIDANCE_PRODUCTION = """For Production:
- Consider scalability, performance, security, reliability, availability, and maintainability."""

PROMPT_ARCHITECTURE_TEMPLATE = """You are a senior software architect.

Using the product name, description, requirements, and stage (MVP or Production), design the most cost-effective architecture.

## Product

- Product name: {product_name}
- Product description: {description}
- Platform: {platform_label}
- Stage: {stage_label}

## Requirements

{requirement_lines}

{stage_guidance}

Think about all required components and include only components justified by the requirements.

Return JSON only.

The JSON must contain:
{{
  "stage": "{stage_label}",
  "components": [],
  "architecture": {{}},
  "diagrams": {{}}
}}

Each component must include:
- name
- type (one of: {component_type_list})
- tag (required or optional)
- description
- cloud_options with keys aws, gcp, and azure — concrete service names for each provider

architecture must include summary (string) and flow (array of strings).

Generate exactly three diagrams under diagrams:

1. high_level — High Level Design
   - Business-level view.
   - Show only core architecture components.
   - Exclude operational components (secrets, config, monitoring, logging, tracing, alerting).
   - Keep minimal and easy to understand.

2. system_flow — System Flow
   - Show request and data flow through the system.
   - Include only components involved in the flow.
   - Exclude operational components.
   
3. technical_architecture — Technical Architecture
   - Complete technical architecture.
   - Include all relevant components.
   - Include operational components when relevant.
   - Show infrastructure, security, observability, and resilience patterns.

    Each diagram must contain:
    - title
    - nodes (id, name, optional group)
    - edges (source, target, optional label)
    
    Node groups:
    - experience
    - platform
    - data
    - operations
    
Generate only the architecture for the requested stage ({stage_label}).
"""


# ---------------------------------------------------------------------------
# Architecture component selection (Step 2)
# ---------------------------------------------------------------------------

COMPONENT_SELECTION_PROMPT_VERSION = "architecture-component-selector-v4"

COMPONENT_SELECTION_SYSTEM_PROMPT = (
    "You are a senior software architect. Given an application, its platform "
    "(web or mobile), and a fixed list of architecture component categories, "
    "decide which categories the application needs. "
    "Business requirement labels in the prompt are not category ids. "
    "Return only valid JSON."
)

# Placeholders use the ``{{token}}`` form and are injected by the prompt builder via
# string replacement (not str.format) so the literal JSON braces below are safe.
PROMPT_COMPONENT_SELECTION_TEMPLATE = """You are a senior software architect.

Decide which architecture component categories the described application needs.

## Application

- Description: {{application_description}}
- Platform: {{platform}}
- Stage: {{stage}}
- Expected users: {{expected_users}}

## Business requirements (context only)

These describe optional product capabilities. They are NOT architecture category ids.
Do not copy requirement names into your response.

{{requirements}}

## Available architecture categories

There are exactly {{category_count}} categories below. Only these categories exist.
Do not invent new ids. The only valid category ids are:
{{valid_category_ids}}

{{architecture_categories}}

## Task

Classify EVERY category above as either "selected" or "excluded". Do not skip any.

### How to decide

- Base your decision on the FULL application described above, including its platform (web or mobile), not only on the requirement flags. The "Requirements" section only captures OPTIONAL capabilities. A requirement that is disabled, absent, or set to false means that specific optional capability is not needed — it does NOT mean the application has no backend, no data layer, or no API.
- Treat platform as a first-class constraint on the client experience and delivery path:
  - web: browser-based clients; include web-facing experience and delivery components when relevant (for example CDN or web client hosting).
  - mobile: native or cross-platform mobile clients installed on devices; favor mobile client, push notification, and device-oriented experience components over browser-only delivery.
- Select every category the described application needs to actually run and serve its core functionality end to end.
- Foundational runtime capabilities are almost always required for any real web, SaaS, or backend application. Interpret each category by its full description, not by one keyword:
  - "compute" runs the application code and APIs (web servers, containers, or serverless functions) — it is far more than background jobs. Any application that runs server-side logic needs compute. Do NOT exclude compute just because background processing is turned off.
  - an API entry point / gateway is needed whenever clients call a backend.
  - a primary data store is needed whenever the application persists user or business data.
- Do not exclude a foundational capability solely because a single optional requirement (such as background processing, file uploads, or real-time) is turned off.
- If a selected component depends on another capability to function, select that supporting capability too.

Rules:
- The combined number of items in "selected" and "excluded" must be exactly {{category_count}}.
- Every category id listed above must appear exactly once, in either "selected" or "excluded".
- Never place the same id in both arrays.
- Never repeat an id.
- Use only the ids from the Available architecture categories list above.
- Never use business requirement names (such as background_processing, payments, realtime,
  dashboards_reports, external_integrations, notifications, or reliability) as category ids.
- When the Notifications requirement is enabled (with channels such as email, push, SMS,
  or in-app), select the notification category.
- "reason" must be a short, non-empty sentence.

Think in terms of the complete runtime architecture needed to run the described application.
Before answering, verify that every id from the list appears exactly once in your response, and that no capability required to run the described application has been left out.

Return JSON only, in exactly this structure:
{
  "selected": [
    {
      "id": "component_id",
      "reason": "Short reason explaining why this component is needed."
    }
  ],
  "excluded": [
    {
      "id": "component_id",
      "reason": "Short reason explaining why this component is not needed."
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Global usage model (Step 3)
# ---------------------------------------------------------------------------

GLOBAL_USAGE_MODEL_PROMPT_VERSION = "global-usage-model-v4"

# Behavioral parameters the global usage model may ask the LLM to estimate.
# Static project inputs (e.g. ``users``) and derived monthly totals are excluded.
GLOBAL_LLM_USAGE_PARAMETERS: tuple[str, ...] = ()

# Short definitions injected next to parameter names in the Step 3 prompt.
USAGE_PARAMETER_GUIDANCE: dict[str, str] = {
    "database_storage_gb": (
        "SQL/NoSQL database storage only (tables, indexes, metadata, history). "
        "Do not include object/file storage or user uploads."
    ),
    "compute_disk_gb": (
        "Local disk attached to compute instances (VMs or persistent volumes). "
        "Do not include database or object storage."
    ),
    "search_storage_gb": (
        "Search index storage only. Do not include database tables or object storage."
    ),
    "cache_storage_gb": (
        "Persistent cache storage (snapshots, AOF, backup volumes). "
        "Do not include in-memory cache sizing, database, or object storage."
    ),
    "capacity_mode": (
        "Azure Cosmos DB pricing mode. Return exactly one of these JSON strings: "
        "Serverless, Provisioned Throughput, Autoscale. Do not return a number."
    ),
    "workload_type": (
        "EC2 instance family for the compute workload. Return exactly one of these "
        "JSON strings: Burstable, General Purpose, Compute Optimized, "
        "Memory Optimized, GPU. Do not return a number."
    ),
    "api_type": (
        "API Gateway API style. Return exactly one of these JSON strings: "
        "HTTP API, REST API, WebSocket API. Do not return a number."
    ),
    "queue_type": (
        "SQS queue type. Return exactly one of these JSON strings: "
        "Standard, FIFO. Do not return a number."
    ),
    "request_units_per_user_per_month": (
        "Average Cosmos DB request units consumed per active user per month. "
        "Required when capacity_mode is Serverless. "
        "If capacity_mode is Provisioned Throughput or Autoscale, omit this "
        "parameter or return 0."
    ),
    "required_ru_per_second": (
        "Provisioned throughput in request units per second. "
        "Required when capacity_mode is Provisioned Throughput or Autoscale. "
        "If capacity_mode is Serverless, omit this parameter or return 0."
    ),
    "notifications_per_user_per_month": (
        "Average outbound notifications sent to each active user per month across all "
        "enabled channels (email, push, SMS, in-app). Use requirements.notifications "
        "when present: if disabled, return 0; if enabled, scale volume by the selected "
        "channels and application type (transactional alerts vs marketing, etc.)."
    ),
    "sms_verifications_per_user_per_month": (
        "Average SMS verification messages sent per active user per month for SMS "
        "authentication (sign-up, sign-in, MFA/OTP). "
        "Look at requirements.authentication.authentication_methods and Known static "
        "inputs. If authentication is disabled OR 'sms' is not listed, return 0. "
        "If 'sms' IS listed, you MUST return a positive number (typically 1.0 for "
        "about one SMS per active user per month; use 2–3 for frequent re-auth). "
        "Never return 0 when SMS authentication is enabled."
    ),
}

COSMOS_DB_CAPACITY_MODES: frozenset[str] = frozenset(
    {"Serverless", "Provisioned Throughput", "Autoscale"}
)
COSMOS_DB_SERVERLESS_MODE = "Serverless"
COSMOS_DB_PROVISIONED_MODES: frozenset[str] = frozenset(
    {"Provisioned Throughput", "Autoscale"}
)

EC2_WORKLOAD_TYPES: frozenset[str] = frozenset(
    {
        "Burstable",
        "General Purpose",
        "Compute Optimized",
        "Memory Optimized",
        "GPU",
    }
)
API_GATEWAY_API_TYPES: frozenset[str] = frozenset(
    {"HTTP API", "REST API", "WebSocket API"}
)
SQS_QUEUE_TYPES: frozenset[str] = frozenset({"Standard", "FIFO"})

# LLM parameters whose value must be a string from a fixed set (not numeric).
STRING_ENUM_USAGE_PARAMETERS: dict[str, frozenset[str]] = {
    "capacity_mode": COSMOS_DB_CAPACITY_MODES,
    "workload_type": EC2_WORKLOAD_TYPES,
    "api_type": API_GATEWAY_API_TYPES,
    "queue_type": SQS_QUEUE_TYPES,
}

# Static parameters resolved from project intake / requirements (never sent to OpenAI).
GLOBAL_STATIC_USAGE_PARAMETERS: tuple[str, ...] = ("users", "stage")

# Monthly totals the system derives later (e.g. users × per-user rate). Never LLM-estimated.
DERIVED_TOTAL_USAGE_PARAMETERS: frozenset[str] = frozenset(
    {
        "requests_per_month",
        "messages_per_month",
        "connection_minutes_per_month",
        "request_units_per_month",
    }
)

GLOBAL_USAGE_MODEL_PROMPT = """
You are a cloud usage analyst.

Estimate the application's monthly usage based on the provided product information.

## Application

Description:
{{application_description}}

Platform:
{{platform}}

Stage:
{{stage}}

Expected users:
{{expected_users}}

Requirements:
{{requirements}}

Known static inputs (already resolved — do not re-estimate these):
{{static_usage_values}}

Selected architecture components:
{{selected_components}}

Usage parameters to estimate:
{{usage_parameters}}

## Task

Estimate only the usage parameters listed above.

Base the estimates on:
- how users are expected to use the product on the stated platform (web or mobile);
- the described application functionality;
- the product stage;
- the expected number of users;
- the requirements and Known static inputs (especially authentication_methods);
- the selected architecture components.

Return realistic baseline estimates for the current stage, not maximum capacity.

Each value must be numeric and non-negative, except string enum parameters
whose guidance lists allowed values — return those as JSON strings exactly.

Return valid JSON only:

{
  "usage": {
    "parameter_name": {
      "value": 0,
      "reason": "Short explanation for the estimate."
    }
  }
}

Rules:
- Return every provided usage parameter exactly once.
- Do not add parameters that were not provided.
- String enum parameters must use one of the allowed string values exactly.
- Numeric parameters must be numbers, not strings.
- Do not calculate cloud prices.
- Do not select cloud services.
- Keep every reason short.
- Storage parameters are scoped by responsibility. Never fold object/file
  storage into database_storage_gb. Object storage is priced separately from
  documents_per_month and average_document_size_mb.
"""


# ---------------------------------------------------------------------------
# Generation lifecycle
# ---------------------------------------------------------------------------

GENERATION_STATUS_PENDING = "pending"
GENERATION_STATUS_COMPLETED = "completed"
GENERATION_STATUS_FAILED = "failed"

GENERATION_STEPS: tuple[str, ...] = (
    "create_request",
    "build_prompt",
    "save_generation_request",
    "call_ai",
    "validate_response",
    "map_payload",
    "estimate_costs",
    "persist_document",
    "complete",
)

COMPONENT_ORDER_MULTIPLIER = 10
COMPONENT_CATEGORY_CORE = "core"
COMPONENT_CATEGORY_OPTIONAL = "optional"

# ---------------------------------------------------------------------------
# Auth / JWT
# ---------------------------------------------------------------------------

JWT_ALGORITHM = "HS256"
OAUTH_PROVIDER_NAME = "google"
OAUTH_SERVER_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"
OAUTH_SCOPES = "openid email profile"
OAUTH_SESSION_COOKIE = "oauth_session"
OAUTH_SESSION_MAX_AGE_SECONDS = 600
SESSION_COOKIE_SAMESITE = "lax"
SESSION_COOKIE_PATH = "/"

# ---------------------------------------------------------------------------
# Reused error / status messages
# ---------------------------------------------------------------------------

ERR_NOT_AUTHENTICATED = "Not authenticated"
ERR_INVALID_SESSION = "Invalid or expired session"
ERR_USER_NOT_FOUND = "User not found"
ERR_PROJECT_NOT_FOUND = "Project not found"
ERR_PROJECT_FORBIDDEN = "Not allowed"
ERR_OAUTH_NOT_CONFIGURED = "Google OAuth is not configured"
ERR_GOOGLE_SUB_MISSING = "Google account id missing"
ERR_OPENAI_KEY_MISSING = "OpenAI API key is not configured. Set OPENAI_API_KEY in backend/.env."
ERR_AI_EMPTY_RESPONSE = "AI returned an empty response."
ERR_AI_RESPONSE_EMPTY = "AI response was empty."
ERR_AI_NO_JSON_OBJECT = "AI response did not contain a JSON object."
ERR_NO_ARCHITECTURE_CATEGORIES = (
    "No architecture categories are configured. Seed the "
    "'architecture_categories' collection before generating components."
)
ERR_COMPONENT_SELECTION_INVALID = "The component selection response was invalid."
ERR_COMPONENT_SELECTION_NOT_JSON = "The component selection response was not valid JSON."
ERR_NO_COMPONENT_SELECTION = (
    "No component selection exists yet. Generate the architecture components first."
)
ERR_SELECTION_NOT_FOUND = "The component selection was not found."
ERR_ARCHITECTURE_CATEGORY_NOT_FOUND = "The selected architecture category was not found."
ERR_COMPONENT_ALREADY_SELECTED = "This component is already in the selected list."
ERR_COMPONENT_NOT_SELECTED = "This component is not in the selected list."
ERR_GLOBAL_USAGE_MODEL_NOT_JSON = "The global usage model response was not valid JSON."
ERR_NO_USAGE_PARAMETERS = (
    "No usage parameters could be resolved for the selected components. "
    "Seed cloud service mappings and pricing services first."
)
ERR_NO_GLOBAL_USAGE_MODEL = (
    "No global usage model exists yet. Generate the global usage model first."
)
ERR_INVALID_CLOUD_PROVIDER = "The cloud provider is not supported."
ERR_PRICING_RUN_NOT_FOUND = "The pricing run was not found."
ERR_NO_PRICING_RUN = "No pricing run exists yet. Generate pricing first."

# ---------------------------------------------------------------------------
# Manual component management (Step 2) reasons
# ---------------------------------------------------------------------------

REASON_COMPONENT_ADDED_BY_USER = "Added by user during review."
REASON_COMPONENT_REMOVED_BY_USER = "Removed by user during review."
