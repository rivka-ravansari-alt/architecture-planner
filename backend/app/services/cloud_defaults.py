"""Default cloud service options when the AI omits or empties a provider list."""

from __future__ import annotations

from .component_types import DEFAULT_COMPONENT_TYPE

_CLOUD_PROVIDERS = ("aws", "gcp", "azure")

_NOT_APPLICABLE = ["N/A — not a managed cloud service"]

_DEFAULTS_BY_TYPE: dict[str, dict[str, list[str]]] = {
    "user": dict.fromkeys(_CLOUD_PROVIDERS, _NOT_APPLICABLE.copy()),
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

_FALLBACK = _DEFAULTS_BY_TYPE["api"]

_PROVIDER_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "aws": ("aws", "amazon", "amazon web services"),
    "gcp": ("gcp", "google", "google cloud", "google cloud platform"),
    "azure": ("azure", "microsoft azure"),
}


def default_cloud_options_for_type(component_type: str) -> dict[str, list[str]]:
    defaults = _DEFAULTS_BY_TYPE.get(component_type) or _FALLBACK
    return {provider: list(defaults[provider]) for provider in _CLOUD_PROVIDERS}


def _options_for_provider(cloud_options: dict, provider: str) -> list:
    direct = cloud_options.get(provider)
    if isinstance(direct, list):
        return direct
    if isinstance(direct, str) and direct.strip():
        return [direct]

    for key, value in cloud_options.items():
        key_lower = str(key).strip().lower()
        if key_lower in _PROVIDER_KEY_ALIASES[provider]:
            if isinstance(value, list):
                return value
            if isinstance(value, str) and value.strip():
                return [value]
    return []


def normalize_cloud_options(component: dict) -> dict[str, list[str]]:
    """Return non-empty aws/gcp/azure lists, filling gaps from type defaults."""
    raw = component.get("cloud_options")
    cloud_options = raw if isinstance(raw, dict) else {}

    component_type = str(component.get("type", DEFAULT_COMPONENT_TYPE)).strip().lower()
    defaults = default_cloud_options_for_type(component_type)

    normalized: dict[str, list[str]] = {}
    for provider in _CLOUD_PROVIDERS:
        options = _options_for_provider(cloud_options, provider)
        cleaned = [str(option).strip() for option in options if str(option).strip()]
        if not cleaned:
            cleaned = list(defaults[provider])
        normalized[provider] = cleaned

    return normalized
