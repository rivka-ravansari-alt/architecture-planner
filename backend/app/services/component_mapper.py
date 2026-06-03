"""Map validated AI JSON to internal keys and cloud mappings."""

from __future__ import annotations

import re
from typing import Any

from .component_types import DEFAULT_COMPONENT_TYPE, VALID_COMPONENT_TYPES
from .types import MappedComponent, MappedRisk

_TYPE_KEY_MAP: dict[str, str] = {
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

_KEY_HINTS: list[tuple[str, tuple[str, ...]]] = [
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


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug[:60] or "component"


def infer_component_key(name: str, used_keys: set[str], component_type: str | None = None) -> str:
    if component_type and component_type in VALID_COMPONENT_TYPES:
        mapped = _TYPE_KEY_MAP.get(component_type)
        if mapped and mapped not in used_keys:
            return mapped
    lower = name.lower()
    for key, hints in _KEY_HINTS:
        if any(hint in lower for hint in hints):
            if key not in used_keys:
                return key
    base = _slugify(name)
    candidate = base
    suffix = 2
    while candidate in used_keys:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


def map_ai_payload(
    payload: dict[str, Any],
) -> tuple[list[MappedComponent], list[MappedRisk], list[str], list[str], str, list[str]]:
    used_keys: set[str] = set()
    components: list[MappedComponent] = []

    for order, item in enumerate(payload["components"]):
        name = str(item["name"]).strip()
        reason = str(item["reason"]).strip()
        optional = str(item["tag"]).strip().lower() == "optional"
        component_type = str(item.get("type", DEFAULT_COMPONENT_TYPE)).strip().lower()
        if component_type not in VALID_COMPONENT_TYPES:
            component_type = DEFAULT_COMPONENT_TYPE
        key = infer_component_key(name, used_keys, component_type)
        used_keys.add(key)
        cloud_options = item["cloud_options"]
        cloud = {
            provider: [str(option).strip() for option in cloud_options.get(provider, []) if str(option).strip()]
            for provider in ("aws", "gcp", "azure")
        }
        components.append(
            MappedComponent(
                key=key,
                name=name,
                component_type=component_type,
                reason=reason,
                category="optional" if optional else "core",
                optional=optional,
                order=order * 10,
                cloud=cloud,
            )
        )

    risks = [
        MappedRisk(
            title=str(risk["title"]).strip(),
            description=str(risk["description"]).strip(),
            severity=str(risk["severity"]).strip().lower(),
        )
        for risk in payload["risks"]
    ]

    return (
        components,
        risks,
        [str(item).strip() for item in payload["recommendations"]],
        [str(item).strip() for item in payload["next_steps"]],
        str(payload["architecture"]["summary"]).strip(),
        [str(step).strip() for step in payload["architecture"]["flow"]],
    )


def feature_flags_from_components(components: list[MappedComponent]) -> dict[str, bool]:
    keys = {c.key for c in components if not c.optional}
    return {
        "file_upload": "object_storage" in keys,
        "ai": "ai_service" in keys,
        "background_processing": "queue_worker" in keys,
    }
