"""Shared test data for AI generation tests."""

from __future__ import annotations

import json


def _option_detail(
    when_to_use: str,
    cost_impact: str,
    pros: list[str],
    cons: list[str],
    *,
    not_applicable: bool = False,
) -> dict[str, object]:
    detail: dict[str, object] = {
        "when_to_use": when_to_use,
        "cost_impact": cost_impact,
        "pros": pros,
        "cons": cons,
    }
    if not_applicable:
        detail["not_applicable"] = True
    return detail


def _na_option(message: str = "Not applicable for this component.") -> dict[str, object]:
    return _option_detail(message, "", [], [], not_applicable=True)


def implementation_options(
    recommended: str,
    *,
    serverless: dict[str, object] | None = None,
    container: dict[str, object] | None = None,
    managed_service: dict[str, object] | None = None,
    external_provider: dict[str, object] | None = None,
) -> dict[str, object]:
    defaults = {
        "serverless": _option_detail(
            "Low or spiky traffic with minimal operations overhead.",
            "Very low at MVP scale; pay per use.",
            ["Minimal ops", "Automatic scaling"],
            ["Cold starts", "Execution limits"],
        ),
        "container": _option_detail(
            "Steady, predictable traffic where always-on compute is cost-effective.",
            "Moderate baseline; can beat serverless at steady load.",
            ["Consistent performance", "Long-running workloads"],
            ["Higher idle cost", "More deployment work"],
        ),
        "managed_service": _option_detail(
            "Default choice when a fully managed platform fits the workload.",
            "Low-to-moderate fixed monthly cost for small workloads.",
            ["Fast to ship", "Built-in maintenance"],
            ["Less fine-grained control"],
        ),
        "external_provider": _option_detail(
            "Third-party SaaS or API when outsourcing is the best fit.",
            "Usage-based or subscription pricing from the vendor.",
            ["Fast integration", "Vendor handles compliance and uptime"],
            ["Vendor lock-in", "Per-seat or API pricing can grow"],
        ),
    }
    overrides = {
        "serverless": serverless,
        "container": container,
        "managed_service": managed_service,
        "external_provider": external_provider,
    }
    options: dict[str, object] = {"recommended": recommended}
    for key, default in defaults.items():
        options[key] = overrides[key] if overrides[key] is not None else default
    return options


VALID_AI_PAYLOAD = {
    "components": [
        {
            "name": "Web Client",
            "type": "web_app",
            "tag": "required",
            "reason": "Users access the product in the browser.",
            "implementation_options": implementation_options(
                "managed_service",
                serverless=_na_option(),
                external_provider=_na_option(),
            ),
            "cloud_options": {
                "aws": ["Amplify Hosting"],
                "gcp": ["Firebase Hosting"],
                "azure": ["Azure App Service"],
            },
        },
        {
            "name": "Backend / API Layer",
            "type": "api",
            "tag": "required",
            "reason": "Central entry point for all client requests.",
            "implementation_options": implementation_options(
                "serverless",
                external_provider=_na_option(),
            ),
            "cloud_options": {
                "aws": ["API Gateway"],
                "gcp": ["API Gateway"],
                "azure": ["API Management"],
            },
        },
        {
            "name": "Authentication Service",
            "type": "authentication",
            "tag": "required",
            "reason": "Handles login and session management.",
            "implementation_options": implementation_options(
                "managed_service",
                serverless=_na_option(),
                container=_na_option(),
            ),
            "cloud_options": {
                "aws": ["Cognito"],
                "gcp": ["Firebase Authentication", "Identity Platform"],
                "azure": ["Entra ID B2C"],
            },
        },
        {
            "name": "Object Storage",
            "type": "object_storage",
            "tag": "optional",
            "reason": "Stores uploaded files when needed.",
            "implementation_options": implementation_options(
                "managed_service",
                serverless=_na_option(),
                container=_na_option(),
                external_provider=_na_option(),
            ),
            "cloud_options": {
                "aws": ["S3"],
                "gcp": ["Cloud Storage"],
                "azure": ["Blob Storage"],
            },
        },
    ],
    "architecture": {
        "summary": "A browser client talks to an API backed by core services.",
        "flow": [
            "User interacts with the web client.",
            "Client calls the API gateway.",
            "API validates auth and runs business logic.",
        ],
    },
    "diagrams": {
        "high_level": {
            "title": "High Level Design",
            "nodes": [
                {"id": "user", "name": "End User", "group": "experience"},
                {"id": "web_client", "name": "Web Client", "group": "experience"},
                {"id": "api_gateway", "name": "API Gateway", "group": "platform"},
                {"id": "auth", "name": "Authentication Service", "group": "platform"},
                {"id": "object_storage", "name": "Object Storage", "group": "data"},
            ],
            "edges": [
                {"source": "user", "target": "web_client"},
                {"source": "web_client", "target": "api_gateway"},
                {"source": "api_gateway", "target": "auth"},
                {"source": "api_gateway", "target": "object_storage"},
            ],
        },
        "system_flow": {
            "title": "System Flow",
            "nodes": [
                {"id": "user", "name": "User"},
                {"id": "sign_in", "name": "Sign In"},
                {"id": "web_client", "name": "Web Client"},
                {"id": "upload", "name": "Upload File"},
                {"id": "object_storage", "name": "Object Storage"},
                {"id": "process", "name": "Process Request"},
            ],
            "edges": [
                {"source": "user", "target": "sign_in"},
                {"source": "sign_in", "target": "web_client"},
                {"source": "web_client", "target": "upload"},
                {"source": "upload", "target": "object_storage"},
                {"source": "web_client", "target": "process"},
            ],
        },
        "technical_architecture": {
            "title": "Technical Architecture",
            "nodes": [
                {"id": "user", "name": "End User", "group": "experience"},
                {"id": "web_client", "name": "Web Client", "group": "experience"},
                {"id": "api_gateway", "name": "API Gateway", "group": "platform"},
                {"id": "auth", "name": "Authentication Service", "group": "platform"},
                {"id": "database", "name": "Database", "group": "data"},
                {"id": "object_storage", "name": "Object Storage", "group": "data"},
                {"id": "monitoring", "name": "Monitoring", "group": "operations", "type": "monitoring"},
                {"id": "logging", "name": "Logging", "group": "operations", "type": "logging"},
            ],
            "edges": [
                {"source": "user", "target": "web_client"},
                {"source": "web_client", "target": "api_gateway"},
                {"source": "api_gateway", "target": "auth"},
                {"source": "api_gateway", "target": "database"},
                {"source": "api_gateway", "target": "object_storage"},
                {"source": "api_gateway", "target": "monitoring"},
                {"source": "api_gateway", "target": "logging"},
            ],
        },
    },
}

VALID_AI_RESPONSE_JSON = json.dumps(VALID_AI_PAYLOAD)

INVALID_AI_RESPONSE_JSON = json.dumps({"components": []})
