"""Application-wide constants and default values (non-secret configuration)."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Validation limits
# ---------------------------------------------------------------------------

DESCRIPTION_MAX_TOKENS = 500
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

VALID_COMPONENT_TYPES: frozenset[str] = frozenset(
    {
        "user",
        "web_app",
        "mobile_app",
        "browser_extension",
        "api",
        "authentication",
        "database",
        "object_storage",
        "queue",
        "worker",
        "ai_service",
        "monitoring",
        "analytics",
        "notification",
        "payment",
    }
)

DEFAULT_COMPONENT_TYPE = "api"
VALID_COMPONENT_TAGS: frozenset[str] = frozenset({"required", "optional"})
VALID_RISK_SEVERITIES: frozenset[str] = frozenset({"low", "medium", "high"})

COMPONENT_TYPE_KEY_MAP: dict[str, str] = {
    "web_app": "client_web",
    "mobile_app": "client_mobile",
    "browser_extension": "client_extension",
    "api": "api_layer",
    "authentication": "auth",
    "database": "database",
    "object_storage": "object_storage",
    "queue": "queue_worker",
    "worker": "queue_worker",
    "ai_service": "ai_service",
    "monitoring": "monitoring",
    "analytics": "analytics",
    "notification": "push_notifications",
    "payment": "payments",
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

DIAGRAM_KEYS: tuple[str, ...] = ("high_level", "system_flow", "technical_flow")

DEFAULT_DIAGRAM_TITLES: dict[str, str] = {
    "high_level": "High Level Architecture",
    "system_flow": "System Flow",
    "technical_flow": "Technical Flow",
}

VALID_DIAGRAM_GROUPS: frozenset[str] = frozenset(
    {"experience", "platform", "data", "operations"}
)

AI_RESPONSE_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "components",
    "architecture",
    "diagrams",
    "risks",
    "recommendations",
    "next_steps",
)

COMPONENT_REQUIRED_FIELDS: tuple[str, ...] = ("name", "type", "tag", "reason")
RISK_REQUIRED_FIELDS: tuple[str, ...] = ("title", "description", "severity")

# ---------------------------------------------------------------------------
# Cloud providers
# ---------------------------------------------------------------------------

CLOUD_PROVIDERS: tuple[str, ...] = ("aws", "gcp", "azure")

CLOUD_PROVIDER_LABELS: dict[str, str] = {
    "aws": "AWS",
    "gcp": "Google Cloud",
    "azure": "Azure",
}

NOT_APPLICABLE_CLOUD: list[str] = ["N/A — not a managed cloud service"]

CLOUD_PROVIDER_ALIASES: dict[str, tuple[str, ...]] = {
    "aws": ("aws", "amazon", "amazon web services"),
    "gcp": ("gcp", "google", "google cloud", "google cloud platform"),
    "azure": ("azure", "microsoft azure"),
}

CLOUD_DEFAULTS_BY_TYPE: dict[str, dict[str, list[str]]] = {
    "user": dict.fromkeys(CLOUD_PROVIDERS, NOT_APPLICABLE_CLOUD.copy()),
    "web_app": {
        "aws": ["CloudFront", "S3", "Amplify Hosting"],
        "gcp": ["Cloud CDN", "Cloud Storage", "Firebase Hosting"],
        "azure": ["Azure CDN", "Static Web Apps", "Blob Storage"],
    },
    "mobile_app": {
        "aws": ["Amplify", "API Gateway", "Cognito"],
        "gcp": ["Firebase", "API Gateway", "Identity Platform"],
        "azure": ["App Service", "API Management", "Entra ID B2C"],
    },
    "browser_extension": {
        "aws": ["API Gateway", "Lambda"],
        "gcp": ["Cloud Run", "API Gateway"],
        "azure": ["API Management", "Azure Functions"],
    },
    "api": {
        "aws": ["API Gateway", "Application Load Balancer"],
        "gcp": ["API Gateway", "Cloud Load Balancing"],
        "azure": ["API Management", "Application Gateway"],
    },
    "authentication": {
        "aws": ["Cognito"],
        "gcp": ["Identity Platform", "Firebase Auth"],
        "azure": ["Entra ID B2C", "Entra ID"],
    },
    "database": {
        "aws": ["RDS", "Aurora", "DynamoDB"],
        "gcp": ["Cloud SQL", "Firestore", "Spanner"],
        "azure": ["Azure SQL", "Cosmos DB", "PostgreSQL Flexible Server"],
    },
    "object_storage": {
        "aws": ["S3"],
        "gcp": ["Cloud Storage"],
        "azure": ["Blob Storage"],
    },
    "queue": {
        "aws": ["SQS", "Amazon MQ"],
        "gcp": ["Pub/Sub", "Cloud Tasks"],
        "azure": ["Service Bus", "Queue Storage"],
    },
    "worker": {
        "aws": ["Lambda", "ECS", "Fargate"],
        "gcp": ["Cloud Run", "Cloud Functions"],
        "azure": ["Azure Functions", "Container Apps"],
    },
    "ai_service": {
        "aws": ["Bedrock", "SageMaker"],
        "gcp": ["Vertex AI", "Gemini API"],
        "azure": ["Azure OpenAI Service", "Azure AI Foundry"],
    },
    "monitoring": {
        "aws": ["CloudWatch", "X-Ray"],
        "gcp": ["Cloud Monitoring", "Cloud Logging"],
        "azure": ["Azure Monitor", "Application Insights"],
    },
    "analytics": {
        "aws": ["QuickSight", "Athena"],
        "gcp": ["Looker", "BigQuery"],
        "azure": ["Power BI", "Azure Synapse Analytics"],
    },
    "notification": {
        "aws": ["SNS", "SES", "Pinpoint"],
        "gcp": ["Firebase Cloud Messaging", "SendGrid via Pub/Sub"],
        "azure": ["Notification Hubs", "Communication Services"],
    },
    "payment": {
        "aws": ["Payment Cryptography", "third-party via Lambda"],
        "gcp": ["Cloud Billing integrations", "partner connectors"],
        "azure": ["Partner integrations", "Logic Apps"],
    },
}

CLOUD_DEFAULTS_FALLBACK_TYPE = "api"

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
# AI generation
# ---------------------------------------------------------------------------

AI_RESPONSE_FORMAT = {"type": "json_object"}
AI_TEMPERATURE = 0.2

AI_SYSTEM_PROMPT = (
    "You are Archsari, a software architecture planning assistant. "
    "Return only valid JSON matching the requested schema."
)

PROMPT_COMPONENT_TYPE_LIST = (
    "user, web_app, mobile_app, browser_extension, api, authentication, database, "
    "object_storage, queue, worker, ai_service, monitoring, analytics, notification, payment"
)

PROMPT_JSON_EXAMPLE = """{
  "components": [
    {
      "name": "Component name",
      "type": "database",
      "tag": "required",
      "reason": "Why this component is needed",
      "cloud_options": {
        "aws": ["Lambda", "ECS"],
        "gcp": ["Cloud Run", "Cloud Functions"],
        "azure": ["App Service", "Functions"]
      }
    }
  ],
  "architecture": {
    "summary": "High-level architecture summary",
    "flow": ["Step 1", "Step 2", "Step 3"]
  },
  "diagrams": {
    "high_level": {
      "title": "High Level Design",
      "nodes": [
        { "id": "user", "name": "End User", "group": "experience" }
      ],
      "edges": [
        { "source": "user", "target": "web_app" }
      ]
    },
    "system_flow": {
      "title": "System Flow",
      "nodes": [{ "id": "user", "name": "User" }],
      "edges": [{ "source": "user", "target": "upload" }]
    },
    "technical_flow": {
      "title": "Technical Flow",
      "nodes": [{ "id": "browser", "name": "Browser" }],
      "edges": [{ "source": "browser", "target": "api_gateway" }]
    }
  },
  "risks": [
    { "title": "Risk title", "description": "Risk description", "severity": "low" }
  ],
  "recommendations": ["Recommendation 1"],
  "next_steps": ["Next step 1"]
}"""

# ---------------------------------------------------------------------------
# Generation lifecycle
# ---------------------------------------------------------------------------

GENERATION_STATUS_PENDING = "pending"
GENERATION_STATUS_COMPLETED = "completed"
GENERATION_STATUS_FAILED = "failed"

GENERATION_STEPS: tuple[str, ...] = (
    "create_request",
    "build_prompt",
    "save_prompt",
    "call_ai",
    "validate_response",
    "save_output",
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
