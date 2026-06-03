"""Shared test data for AI generation tests."""

from __future__ import annotations

import json

VALID_AI_PAYLOAD = {
    "components": [
        {
            "name": "Web Client",
            "type": "web_app",
            "tag": "required",
            "reason": "Users access the product in the browser.",
            "cloud_options": {
                "aws": ["CloudFront", "S3"],
                "gcp": ["Cloud CDN", "Cloud Storage"],
                "azure": ["Azure CDN", "Static Web Apps"],
            },
        },
        {
            "name": "API Gateway",
            "type": "api",
            "tag": "required",
            "reason": "Central entry point for all client requests.",
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
            "cloud_options": {
                "aws": ["Cognito"],
                "gcp": ["Identity Platform", "Firebase Auth"],
                "azure": ["Entra ID B2C"],
            },
        },
        {
            "name": "Object Storage",
            "type": "object_storage",
            "tag": "optional",
            "reason": "Stores uploaded files when needed.",
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
                {"id": "user", "name": "End User"},
                {"id": "web_client", "name": "Web Client"},
                {"id": "api_gateway", "name": "API Gateway"},
                {"id": "auth", "name": "Authentication Service"},
                {"id": "object_storage", "name": "Object Storage"},
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
        "technical_flow": {
            "title": "Technical Flow",
            "nodes": [
                {"id": "browser", "name": "Browser"},
                {"id": "api_gateway", "name": "API Gateway"},
                {"id": "auth", "name": "Authentication Service"},
                {"id": "app_service", "name": "Application Service"},
                {"id": "queue", "name": "Processing Queue"},
                {"id": "object_storage", "name": "Object Storage"},
            ],
            "edges": [
                {"source": "browser", "target": "api_gateway"},
                {"source": "api_gateway", "target": "auth"},
                {"source": "api_gateway", "target": "app_service"},
                {"source": "app_service", "target": "queue"},
                {"source": "queue", "target": "object_storage"},
            ],
        },
    },
    "risks": [
        {
            "title": "Session hijacking",
            "description": "Stolen tokens could allow account takeover.",
            "severity": "high",
        }
    ],
    "recommendations": [
        "Use a managed identity provider.",
        "Add rate limiting on public endpoints.",
    ],
    "next_steps": [
        "Confirm the component list with stakeholders.",
        "Pick a cloud provider and provision core services.",
    ],
}

VALID_AI_RESPONSE_JSON = json.dumps(VALID_AI_PAYLOAD)

INVALID_AI_RESPONSE_JSON = json.dumps({"components": []})
