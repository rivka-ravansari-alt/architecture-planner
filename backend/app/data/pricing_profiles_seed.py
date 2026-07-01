"""Default pricing profiles for ArchSari cost calculation."""

from __future__ import annotations

from typing import Any

from app.config.params import (
    PRICING_MODEL_COMPUTE_REQUEST,
    PRICING_MODEL_DATABASE_REQUEST,
    PRICING_MODEL_INSTANCE,
    PRICING_MODEL_MONITORING,
    PRICING_MODEL_NOTIFICATION,
    PRICING_MODEL_STORAGE,
    PRICING_MODEL_TOKEN,
)
from app.services.cost_calculation.pricing_profile_repository import profile_doc_id

_COMPUTE_BILLABLE = {
    "cpu": {"usage_metric": "cpu_seconds", "conversion": "seconds_to_hours"},
    "memory": {"usage_metric": "memory_gib_seconds", "conversion": "gib_seconds_to_gib_hours"},
    "requests": {"usage_metric": "monthly_requests", "conversion": "per_million"},
}

_COMPUTE_IGNORED = ("network", "premium", "spot")

_STORAGE_BILLABLE = {
    "storage": {"usage_metric": "storage_gb", "conversion": "none"},
}

_DATABASE_BILLABLE = {
    "reads": {"usage_metric": "database_reads", "conversion": "per_million"},
    "writes": {"usage_metric": "database_writes", "conversion": "per_million"},
    "storage": {"usage_metric": "database_storage_gb", "conversion": "none"},
}

_INSTANCE_BILLABLE = {
    "instance": {"usage_metric": "instances", "conversion": "none"},
    "hour": {"usage_metric": "instance_hours", "conversion": "none"},
}

_TOKEN_BILLABLE = {
    "input_tokens": {"usage_metric": "input_tokens", "conversion": "tokens_per_1k"},
    "output_tokens": {"usage_metric": "output_tokens", "conversion": "tokens_per_1k"},
}

_NOTIFICATION_BILLABLE = {
    "email": {"usage_metric": "emails_sent", "conversion": "per_thousand"},
    "sms": {"usage_metric": "sms_messages", "conversion": "none"},
    "push": {"usage_metric": "push_notifications", "conversion": "per_thousand"},
}

_MONITORING_BILLABLE = {
    "log": {"usage_metric": "log_gb", "conversion": "none"},
    "metrics": {"usage_metric": "metric_samples", "conversion": "per_thousand"},
}

_SERVICE_PROFILE_OVERRIDES: dict[str, dict[str, Any]] = {
    # GCP
    "Cloud Run": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": _COMPUTE_BILLABLE, "ignored_sku_roles": _COMPUTE_IGNORED},
    "Cloud Run Functions": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": _COMPUTE_BILLABLE, "ignored_sku_roles": _COMPUTE_IGNORED},
    "API Gateway": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": {"requests": _COMPUTE_BILLABLE["requests"]}},
    "Cloud Firestore": {"pricing_model": PRICING_MODEL_DATABASE_REQUEST, "billable_skus": _DATABASE_BILLABLE},
    "Cloud SQL": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Cloud Storage": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Cloud Pub/Sub": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"publish": {"usage_metric": "push_notifications", "conversion": "per_thousand"}}},
    "Cloud Tasks": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": {"requests": _COMPUTE_BILLABLE["requests"]}},
    "Secret Manager": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Cloud Monitoring": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": _MONITORING_BILLABLE, "ignored_sku_roles": ("voice_core", "notification_hubs", "data_ingestion")},
    "Cloud Logging": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"log": _MONITORING_BILLABLE["log"]}},
    "Gemini API": {"pricing_model": PRICING_MODEL_TOKEN, "billable_skus": _TOKEN_BILLABLE},
    "Vertex AI": {"pricing_model": PRICING_MODEL_TOKEN, "billable_skus": _TOKEN_BILLABLE},
    "Firebase Hosting": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Firebase": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": _NOTIFICATION_BILLABLE},
    "SendGrid": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"email": _NOTIFICATION_BILLABLE["email"]}},
    "Networking": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Cloud Memorystore for Redis": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "BigQuery": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Looker Studio": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Vertex AI Search": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Cloud Trace": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"metrics": _MONITORING_BILLABLE["metrics"]}},
    # AWS
    "Lambda": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": _COMPUTE_BILLABLE, "ignored_sku_roles": _COMPUTE_IGNORED},
    "ECS Fargate": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": _COMPUTE_BILLABLE, "ignored_sku_roles": _COMPUTE_IGNORED},
    "API Gateway": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": {"requests": _COMPUTE_BILLABLE["requests"]}},
    "DynamoDB": {"pricing_model": PRICING_MODEL_DATABASE_REQUEST, "billable_skus": _DATABASE_BILLABLE},
    "RDS": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "S3": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "SQS": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"requests": {"usage_metric": "monthly_requests", "conversion": "per_million"}}},
    "SNS": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": _NOTIFICATION_BILLABLE},
    "SES": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"email": _NOTIFICATION_BILLABLE["email"]}},
    "CloudWatch": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": _MONITORING_BILLABLE},
    "CloudWatch Logs": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"log": _MONITORING_BILLABLE["log"]}},
    "CloudWatch Alarms": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"metrics": _MONITORING_BILLABLE["metrics"]}},
    "CloudWatch Dashboards": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"metrics": _MONITORING_BILLABLE["metrics"]}},
    "CloudFront": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Secrets Manager": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Bedrock": {"pricing_model": PRICING_MODEL_TOKEN, "billable_skus": _TOKEN_BILLABLE},
    "Amplify": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Amplify Hosting": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Application Load Balancer": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "ElastiCache": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "OpenSearch Service": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Athena": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "QuickSight": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "SSM Parameter Store": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "AppConfig": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "X-Ray": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"metrics": _MONITORING_BILLABLE["metrics"]}},
    # Azure
    "Functions": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": _COMPUTE_BILLABLE, "ignored_sku_roles": _COMPUTE_IGNORED},
    "Azure Container Apps": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": _COMPUTE_BILLABLE, "ignored_sku_roles": _COMPUTE_IGNORED},
    "Azure App Service": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "API Management": {"pricing_model": PRICING_MODEL_COMPUTE_REQUEST, "billable_skus": {"requests": _COMPUTE_BILLABLE["requests"]}},
    "Azure Cosmos DB": {"pricing_model": PRICING_MODEL_DATABASE_REQUEST, "billable_skus": _DATABASE_BILLABLE},
    "SQL Database": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Blob Storage": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Queue Storage": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"requests": {"usage_metric": "monthly_requests", "conversion": "per_million"}}},
    "Service Bus": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"requests": {"usage_metric": "monthly_requests", "conversion": "per_million"}}},
    "Azure Monitor": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": _MONITORING_BILLABLE, "ignored_sku_roles": ("voice_core", "notification_hubs", "data_ingestion")},
    "Log Analytics": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": {"log": _MONITORING_BILLABLE["log"]}},
    "Notification Hubs": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": _NOTIFICATION_BILLABLE},
    "Foundry Models": {"pricing_model": PRICING_MODEL_TOKEN, "billable_skus": _TOKEN_BILLABLE},
    "Application Gateway": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Content Delivery Network": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Application Insights": {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": _MONITORING_BILLABLE},
    "Azure App Center": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Azure Cognitive Search": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Key Vault": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "App Configuration": {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE},
    "Redis Cache": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Power BI": {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE},
    "Voice Core": {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": {"sms": _NOTIFICATION_BILLABLE["sms"]}},
}


def _infer_profile(service_name: str) -> dict[str, Any]:
    lowered = service_name.casefold()
    if service_name in _SERVICE_PROFILE_OVERRIDES:
        return _SERVICE_PROFILE_OVERRIDES[service_name]

    if any(token in lowered for token in ("storage", "s3", "blob")):
        return {"pricing_model": PRICING_MODEL_STORAGE, "billable_skus": _STORAGE_BILLABLE}
    if any(token in lowered for token in ("lambda", "fargate", "cloud run", "functions", "container apps")):
        return {
            "pricing_model": PRICING_MODEL_COMPUTE_REQUEST,
            "billable_skus": _COMPUTE_BILLABLE,
            "ignored_sku_roles": _COMPUTE_IGNORED,
        }
    if any(token in lowered for token in ("firestore", "dynamodb", "cosmos", "database")):
        return {"pricing_model": PRICING_MODEL_DATABASE_REQUEST, "billable_skus": _DATABASE_BILLABLE}
    if any(token in lowered for token in ("monitor", "cloudwatch", "log analytics", "logging", "trace", "insights")):
        return {"pricing_model": PRICING_MODEL_MONITORING, "billable_skus": _MONITORING_BILLABLE}
    if any(token in lowered for token in ("notification", "sns", "ses", "pub/sub", "sendgrid", "voice")):
        return {"pricing_model": PRICING_MODEL_NOTIFICATION, "billable_skus": _NOTIFICATION_BILLABLE}
    if any(token in lowered for token in ("bedrock", "gemini", "vertex ai", "foundry", "openai")):
        return {"pricing_model": PRICING_MODEL_TOKEN, "billable_skus": _TOKEN_BILLABLE}
    if any(token in lowered for token in ("gateway", "api management")):
        return {
            "pricing_model": PRICING_MODEL_COMPUTE_REQUEST,
            "billable_skus": {"requests": _COMPUTE_BILLABLE["requests"]},
        }
    return {"pricing_model": PRICING_MODEL_INSTANCE, "billable_skus": _INSTANCE_BILLABLE}


def build_pricing_profile_doc(provider: str, service_name: str) -> dict[str, Any]:
    template = _infer_profile(service_name)
    doc_id = profile_doc_id(service_name)
    return {
        "id": doc_id,
        "provider": provider,
        "service_name": service_name,
        "pricing_model": template["pricing_model"],
        "billable_skus": template["billable_skus"],
        "ignored_sku_roles": list(template.get("ignored_sku_roles", ())),
        "enabled": True,
    }


def collect_catalog_service_names() -> dict[str, list[str]]:
    from app.config.params import CLOUD_OPTION_SKIP_VALUES
    from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
    from app.pricing_ingestion.models.aws_catalog_ref import aws_option_display_name
    from app.pricing_ingestion.models.azure_catalog_ref import azure_option_display_name

    names_by_provider: dict[str, set[str]] = {"gcp": set(), "aws": set(), "azure": set()}
    for entry in COMPONENT_CATALOG_SEED:
        for option in entry.get("aws_options", []):
            name = aws_option_display_name(option)
            if name and name.casefold() not in CLOUD_OPTION_SKIP_VALUES:
                names_by_provider["aws"].add(name)
        for option in entry.get("gcp_options", []):
            name = str(option).strip()
            if name and name.casefold() not in CLOUD_OPTION_SKIP_VALUES:
                names_by_provider["gcp"].add(name)
        for option in entry.get("azure_options", []):
            name = azure_option_display_name(option)
            if name and name.casefold() not in CLOUD_OPTION_SKIP_VALUES:
                names_by_provider["azure"].add(name)

    return {
        provider: sorted(names, key=str.casefold)
        for provider, names in names_by_provider.items()
    }


def all_pricing_profile_docs() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for provider, names in collect_catalog_service_names().items():
        for service_name in names:
            docs.append(build_pricing_profile_doc(provider, service_name))
    return docs
