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

CLOUD_PROVIDER_LABELS: dict[str, str] = {
    "aws": "AWS",
    "gcp": "Google Cloud",
    "azure": "Azure",
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
# Object storage (AI generation artifacts)
# ---------------------------------------------------------------------------

COST_CURRENCY = "USD"
STAGE_PRODUCTION = "production"

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
