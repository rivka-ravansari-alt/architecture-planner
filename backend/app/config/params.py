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

APPLICATION_PLATFORM_WEB = "web_app"
APPLICATION_PLATFORM_MOBILE = "mobile_app"

APPLICATION_PLATFORM_LABELS: dict[str, str] = {
    "web": "Web Application",
    "mobile": "Mobile Application",
    "both": "Both Web and Mobile",
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

COMPONENT_CATEGORY_MAIN = "main_architecture"
COMPONENT_CATEGORY_SUPPORTING = "supporting_infrastructure"
VALID_COMPONENT_CATEGORIES: frozenset[str] = frozenset(
    {COMPONENT_CATEGORY_MAIN, COMPONENT_CATEGORY_SUPPORTING}
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

COMPONENT_TYPE_ALIASES: dict[str, str] = {
    "api": "api_gateway",
    "authentication": "auth",
    "ai_service": "ai_provider",
    "integration": "external_api",
}

DEFAULT_COMPONENT_TYPE = "api_gateway"
VALID_COMPONENT_TAGS: frozenset[str] = frozenset({"required", "optional"})

COMPONENT_SOURCE_AI = "ai_generated"
COMPONENT_SOURCE_USER = "user_added"
VALID_COMPONENT_SOURCES: frozenset[str] = frozenset(
    {COMPONENT_SOURCE_AI, COMPONENT_SOURCE_USER}
)

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

CLOUD_DEFAULTS_FALLBACK_TYPE = "api_gateway"

# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

COST_CURRENCY = "USD"
CALCULATOR_VERSION_PROFILE_DRIVEN = "baseline_usage_v1"

COST_ESTIMATE_LOW_FACTOR = 0.75
COST_ESTIMATE_HIGH_FACTOR = 1.35

# Sanity thresholds for small user tiers.
COST_SANITY_REQUIRED_MAX_100_USERS = 500.0
COST_SANITY_OPTIONAL_MAX_100_USERS = 500.0
COST_SANITY_COMPONENT_MAX_100_USERS = 200.0
COST_SANITY_COMPONENT_MAX_1000_USERS = 1000.0

# Usage estimation — conservative baseline defaults (provider-independent).
# Totals are derived by UsageEstimator from users × usage profile × stage.
USAGE_ESTIMATION_BASE: dict[str, float] = {
    "sessions_per_user_month": 10.0,
    "requests_per_session": 3.0,
    "avg_request_duration_seconds": 0.3,
    "cpu_vcpu_per_request": 1.0,
    "memory_gib_per_request": 0.5,
    "db_reads_per_request": 2.0,
    "db_writes_per_request": 0.2,
    "base_storage_gb": 0.1,
    "storage_gb_per_user_upload": 0.0,
    "outbound_gb_per_user": 0.02,
    "base_database_storage_gb": 0.1,
    "database_storage_gb_per_100_users": 1.0,
    "db_storage_gb_per_user": 0.0,
    "queue_messages_per_user": 3.0,
    "cache_memory_gb": 0.25,
    "ai_requests_per_user": 2.0,
    "input_tokens_per_ai_request": 500.0,
    "output_tokens_per_ai_request": 200.0,
    "emails_per_user": 2.0,
    "push_notifications_per_user": 5.0,
    "sms_per_user": 0.5,
    "log_gb_per_1000_requests": 0.05,
    "metric_samples_per_request": 0.5,
    "monitoring_log_gb_cap": 0.5,
    "monitoring_metric_samples_cap": 5000.0,
    "instances": 0.0,
    "instance_hours": 0.0,
    "instance_hours_full": 720.0,
    "hosting_instance_hours_cap": 72.0,
    "active_days_per_month": 25.0,
}

# Questionnaire answer → numeric consumption assumptions for UsageEstimator.
USAGE_PROFILE_MAU: dict[str, float] = {
    "100": 100.0,
    "1000": 1000.0,
    "10000": 10000.0,
    "100000+": 100000.0,
}

USAGE_PROFILE_USER_ACTIVITY: dict[str, float] = {
    "light": 3.0,
    "moderate": 12.0,
    "heavy": 50.0,
    "very_heavy": 150.0,
    # Legacy aliases
    "low": 3.0,
    "medium": 12.0,
    "high": 50.0,
    "very_high": 150.0,
}

USAGE_PROFILE_FILES_PER_MONTH: dict[str, float] = {
    "under_1k": 500.0,
    "1k_10k": 5000.0,
    "10k_100k": 50000.0,
    "100k_plus": 200000.0,
}

USAGE_PROFILE_FILE_SIZE_GB: dict[str, float] = {
    "small": 0.001,
    "medium": 0.005,
    "large": 0.05,
}

USAGE_PROFILE_AI_REQUESTS_PER_USER_DAY: dict[str, float] = {
    "under_1": 0.5,
    "1_5": 3.0,
    "5_20": 12.0,
    "20_plus": 50.0,
}

USAGE_PROFILE_TOKEN_SIZES: dict[str, float] = {
    "small": 250.0,
    "medium": 1000.0,
    "large": 4000.0,
}

USAGE_PROFILE_BACKGROUND_MULTIPLIER: dict[str, float] = {
    "none": 0.0,
    "low": 1.0,
    "moderate": 3.0,
    "heavy": 10.0,
    # Legacy aliases
    "medium": 3.0,
    "high": 10.0,
}

USAGE_PROFILE_NOTIFICATION_VOLUME: dict[str, float] = {
    "under_1k": 500.0,
    "1k_10k": 5000.0,
    "10k_100k": 50000.0,
    "100k_plus": 200000.0,
}

# Capability toggles scale specific consumption dimensions (multiplicative).
USAGE_CAPABILITY_MULTIPLIERS: dict[str, dict[str, float]] = {
    "file_upload": {
        "storage_gb": 2.5,
        "outbound_network_gb": 1.5,
        "monthly_requests": 1.1,
    },
    "background_processing": {
        "queue_messages": 4.0,
        "monthly_requests": 1.15,
        "cpu_seconds": 1.2,
    },
    "dashboards": {
        "database_reads": 1.5,
        "monthly_requests": 1.1,
        "metric_samples": 2.0,
    },
    "ai": {
        "ai_requests": 1.0,
        "input_tokens": 1.0,
        "output_tokens": 1.0,
        "monthly_requests": 1.05,
    },
    "payments": {
        "monthly_requests": 1.1,
        "database_writes": 1.3,
    },
    "auth": {
        "database_reads": 1.2,
        "database_writes": 1.15,
        "monthly_requests": 1.05,
    },
}

USAGE_STAGE_PRODUCTION_MULTIPLIER = 1.5

# Legacy static profiles — kept for reference; prefer UsageEstimator.
USAGE_PROFILE_BY_EXPECTED_USERS: dict[str, dict[str, float]] = {
    "100": {
        "monthly_active_users": 100,
        "monthly_requests": 3_000,
        "avg_request_duration_hours": 0.2 / 3600,
        "cpu_vcpu": 0.25,
        "memory_gib": 0.5,
        "monthly_gb_seconds": 150,
        "storage_gb": 5,
        "egress_gb": 2,
        "database_requests": 10_000,
        "tokens": 50_000,
        "notifications": 500,
        "metric_samples": 10_000,
        "log_gb": 1,
        "instances": 1,
        "instance_hours": 720,
    },
    "1000": {
        "monthly_active_users": 1_000,
        "monthly_requests": 30_000,
        "avg_request_duration_hours": 0.2 / 3600,
        "cpu_vcpu": 0.25,
        "memory_gib": 0.5,
        "monthly_gb_seconds": 1_500,
        "storage_gb": 25,
        "egress_gb": 15,
        "database_requests": 100_000,
        "tokens": 500_000,
        "notifications": 5_000,
        "metric_samples": 50_000,
        "log_gb": 5,
        "instances": 1,
        "instance_hours": 720,
    },
    "10000": {
        "monthly_active_users": 10_000,
        "monthly_requests": 300_000,
        "avg_request_duration_hours": 0.15 / 3600,
        "cpu_vcpu": 0.5,
        "memory_gib": 1.0,
        "monthly_gb_seconds": 15_000,
        "storage_gb": 100,
        "egress_gb": 80,
        "database_requests": 1_000_000,
        "tokens": 5_000_000,
        "notifications": 50_000,
        "metric_samples": 200_000,
        "log_gb": 20,
        "instances": 2,
        "instance_hours": 1_440,
    },
    "100000+": {
        "monthly_active_users": 100_000,
        "monthly_requests": 3_000_000,
        "avg_request_duration_hours": 0.1 / 3600,
        "cpu_vcpu": 1.0,
        "memory_gib": 2.0,
        "monthly_gb_seconds": 150_000,
        "storage_gb": 500,
        "egress_gb": 400,
        "database_requests": 10_000_000,
        "tokens": 50_000_000,
        "notifications": 500_000,
        "metric_samples": 1_000_000,
        "log_gb": 100,
        "instances": 4,
        "instance_hours": 2_880,
    },
}

PRICING_MODEL_COMPUTE_REQUEST = "compute_request_based"
PRICING_MODEL_STORAGE = "storage_based"
PRICING_MODEL_DATABASE_REQUEST = "database_request_based"
PRICING_MODEL_INSTANCE = "instance_based"
PRICING_MODEL_TOKEN = "token_based"
PRICING_MODEL_NOTIFICATION = "notification_based"
PRICING_MODEL_MONITORING = "monitoring_based"
PRICING_MODEL_LINEAR_SKU = "linear_sku"

CLOUD_OPTION_SKIP_VALUES: frozenset[str] = frozenset({"n/a", "stripe", "paddle", "third-party api"})

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
# Firestore (GCP catalog ingestion)
# ---------------------------------------------------------------------------

FIRESTORE_COLLECTION_GCP_CATALOG = "gcp_catalog"
FIRESTORE_COLLECTION_AWS_CATALOG = "aws_catalog"
FIRESTORE_COLLECTION_AZURE_CATALOG = "azure_catalog"
FIRESTORE_COLLECTION_GCP_PRICING_PROFILES = "gcp_pricing_profiles"
FIRESTORE_COLLECTION_AWS_PRICING_PROFILES = "aws_pricing_profiles"
FIRESTORE_COLLECTION_AZURE_PRICING_PROFILES = "azure_pricing_profiles"
# Legacy single-collection name (migrated by seed_pricing_profiles.py)
FIRESTORE_COLLECTION_PRICING_PROFILES = "pricing_profiles"
FIRESTORE_COLLECTION_PRICE_IMPORT_RUNS = "price_import_runs"

PRICING_PROVIDER_GCP = "gcp"
PRICING_PROVIDER_AWS = "aws"
PRICING_PROVIDER_AZURE = "azure"
PRICING_PROVIDER_ALL = "all"
PRICING_PROVIDERS = (
    PRICING_PROVIDER_GCP,
    PRICING_PROVIDER_AWS,
    PRICING_PROVIDER_AZURE,
)

PRICING_PROFILE_COLLECTION_BY_PROVIDER = {
    PRICING_PROVIDER_GCP: FIRESTORE_COLLECTION_GCP_PRICING_PROFILES,
    PRICING_PROVIDER_AWS: FIRESTORE_COLLECTION_AWS_PRICING_PROFILES,
    PRICING_PROVIDER_AZURE: FIRESTORE_COLLECTION_AZURE_PRICING_PROFILES,
}

GCP_CATALOG_SKIP_OPTIONS: frozenset[str] = frozenset(
    {
        "N/A",
        "Stripe",
        "Paddle",
        "Third-party API",
        "SendGrid",
        "Looker Studio",
    }
)

AZURE_CATALOG_SKIP_OPTIONS: frozenset[str] = frozenset(
    {
        "N/A",
        "Stripe",
        "Paddle",
        "Third-party API",
    }
)

AWS_CATALOG_SKIP_OPTIONS: frozenset[str] = frozenset(
    {
        "N/A",
        "Stripe",
        "Paddle",
        "Third-party API",
    }
)

PRICE_IMPORT_STATUS_RUNNING = "running"
PRICE_IMPORT_STATUS_COMPLETED = "completed"
PRICE_IMPORT_STATUS_COMPLETED_WITH_ERRORS = "completed_with_errors"
PRICE_IMPORT_STATUS_FAILED = "failed"

MAX_SKUS_PER_COMPONENT = 80
MAX_SKU_DESCRIPTION_CHARS = 120

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

PROMPT_STAGE_GUIDANCE_MVP = """For MVP:
- Prefer simple, managed, and serverless services.
- Avoid over-engineering."""

PROMPT_STAGE_GUIDANCE_PRODUCTION = """For Production:
- Consider scalability, performance, security, reliability, availability, and maintainability."""

PROMPT_COMPONENTS_TEMPLATE = """You are a senior software architect.

Using the product name, description, application platform, usage profile, and stage (MVP or Production), identify the architecture components needed for this product.

## Product

- Product name: {product_name}
- Product description: {description}
- Application platform: {platform_label}
- Stage: {stage_label}

## Platform considerations
            
The application platform must influence component selection.

When choosing components, consider:
- How users access the product.
- Platform-specific requirements and capabilities.
- Services needed to support the selected platform.

The return components should represent a complete runnable architecture.
Include all components required for the system to function end-to-end, not only components explicitly mentioned in the usage profile.

## Usage profile
{requirement_lines}

{stage_guidance}

## Component catalog
Use only component types from this catalog. Each entry shows the type name followed by its description:
{component_catalog}

Return JSON only.

The JSON must contain:
{{
  "components": []
}}

Each component must include:
- name
- type (one of: {component_type_list})
- tag (required or optional)


"""

PROMPT_DIAGRAMS_TEMPLATE = """You are a senior software architect.

Using the product description and the approved architecture components below, generate architecture diagrams and documentation.

## Product

- Product name: {product_name}
- Product description: {description}
- Stage: {stage_label}

## Approved components

{component_lines}

Return JSON only.

The JSON must contain:
{{
  "architecture": {{}},
  "diagrams": {{}}
}}

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

Use only the approved components listed above. Do not add new components.
"""


# ---------------------------------------------------------------------------
# Generation lifecycle
# ---------------------------------------------------------------------------

GENERATION_STATUS_PENDING = "pending"
GENERATION_STATUS_COMPLETED = "completed"
GENERATION_STATUS_FAILED = "failed"

WORKFLOW_STATUS_DRAFT = "DRAFT"
WORKFLOW_STATUS_COMPONENTS_GENERATED = "COMPONENTS_GENERATED"
WORKFLOW_STATUS_COMPONENTS_APPROVED = "COMPONENTS_APPROVED"
WORKFLOW_STATUS_DIAGRAMS_GENERATED = "DIAGRAMS_GENERATED"
WORKFLOW_STATUS_ARCHITECTURE_APPROVED = "ARCHITECTURE_APPROVED"
WORKFLOW_STATUS_PRICING_GENERATED = "PRICING_GENERATED"

WORKFLOW_ALLOWED_FOR_UPDATE_COMPONENTS: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_COMPONENTS_GENERATED,
        WORKFLOW_STATUS_COMPONENTS_APPROVED,
        WORKFLOW_STATUS_DIAGRAMS_GENERATED,
        WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        WORKFLOW_STATUS_PRICING_GENERATED,
    }
)

WORKFLOW_REQUIRES_DIAGRAM_CLEAR_ON_COMPONENT_UPDATE: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_DIAGRAMS_GENERATED,
        WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        WORKFLOW_STATUS_PRICING_GENERATED,
    }
)

WORKFLOW_ALLOWED_FOR_GENERATE_COMPONENTS: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_DRAFT,
        WORKFLOW_STATUS_COMPONENTS_GENERATED,
        WORKFLOW_STATUS_COMPONENTS_APPROVED,
        WORKFLOW_STATUS_DIAGRAMS_GENERATED,
        WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        WORKFLOW_STATUS_PRICING_GENERATED,
    }
)

WORKFLOW_ALLOWED_FOR_GENERATE_DIAGRAMS: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_COMPONENTS_APPROVED,
        WORKFLOW_STATUS_DIAGRAMS_GENERATED,
        WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        WORKFLOW_STATUS_PRICING_GENERATED,
    }
)

WORKFLOW_ALLOWED_FOR_GENERATE_PRICING: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        WORKFLOW_STATUS_PRICING_GENERATED,
    }
)

WORKFLOW_ALLOWED_FOR_APPROVE_ARCHITECTURE: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_DIAGRAMS_GENERATED,
        WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
        WORKFLOW_STATUS_PRICING_GENERATED,
    }
)

WORKFLOW_ALLOWED_FOR_SKIP_ARCHITECTURE: frozenset[str] = frozenset(
    {
        WORKFLOW_STATUS_COMPONENTS_APPROVED,
    }
)

ERR_INVALID_WORKFLOW_STATUS = "Project is not in the correct workflow stage for this operation."

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
