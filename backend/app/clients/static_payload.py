"""Static architecture JSON used when OpenAI calls are disabled."""

from __future__ import annotations


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


def _implementation_options(recommended: str, **overrides: dict[str, object]) -> dict[str, object]:
    options: dict[str, object] = {
        "recommended": recommended,
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
    options.update(overrides)
    options["recommended"] = recommended
    return options


STATIC_AI_PAYLOAD: dict = {
    "components": [
        {
            "name": "Web Client",
            "type": "web_app",
            "tag": "required",
            "reason": "Provides the user interface for interacting with the product.",
            "implementation_options": _implementation_options(
                "managed_service",
                serverless=_na_option(),
                external_provider=_na_option(),
            ),
            "cloud_options": {
                "aws": ["Amplify Hosting"],
                "gcp": ["Firebase Hosting"],
                "azure": ["Azure Static Web Apps"],
            },
        },
        {
            "name": "Backend / API Layer",
            "type": "api",
            "tag": "required",
            "reason": "Central entry point for client requests and service routing.",
            "implementation_options": _implementation_options(
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
            "name": "Application Service",
            "type": "service",
            "tag": "optional",
            "reason": "Runs core business logic when separated from the API tier.",
            "implementation_options": _implementation_options("serverless"),
            "cloud_options": {
                "aws": ["Lambda", "ECS Fargate"],
                "gcp": ["Cloud Run", "Cloud Functions"],
                "azure": ["Azure Functions", "Container Apps"],
            },
        },
        {
            "name": "Authentication Service",
            "type": "authentication",
            "tag": "required",
            "reason": "Handles user sign-up, login, and session management.",
            "implementation_options": _implementation_options(
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
            "name": "Database",
            "type": "database",
            "tag": "required",
            "reason": "Stores application data with durable, queryable persistence.",
            "implementation_options": _implementation_options(
                "managed_service",
                external_provider=_na_option(),
            ),
            "cloud_options": {
                "aws": ["DynamoDB", "RDS"],
                "gcp": ["Firestore", "Cloud SQL"],
                "azure": ["Cosmos DB", "Azure SQL Database"],
            },
        },
        {
            "name": "Object Storage",
            "type": "object_storage",
            "tag": "optional",
            "reason": "Stores uploaded files and static assets when file uploads are needed.",
            "implementation_options": _implementation_options(
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
        {
            "name": "Background Worker",
            "type": "worker",
            "tag": "optional",
            "reason": "Processes long-running or async jobs outside the request path.",
            "implementation_options": _implementation_options("serverless"),
            "cloud_options": {
                "aws": ["Lambda", "ECS Fargate"],
                "gcp": ["Cloud Run Jobs", "Cloud Functions"],
                "azure": ["Azure Functions", "Container Apps Jobs"],
            },
        },
        {
            "name": "Monitoring and Logging",
            "type": "monitoring",
            "tag": "optional",
            "reason": "Tracks health, metrics, and logs for production operations.",
            "implementation_options": _implementation_options(
                "managed_service",
                serverless=_na_option(),
                container=_na_option(),
                external_provider=_na_option(),
            ),
            "cloud_options": {
                "aws": ["CloudWatch"],
                "gcp": ["Cloud Monitoring"],
                "azure": ["Azure Monitor"],
            },
        },
    ],
    "architecture": {
        "summary": (
            "A browser client communicates with an API layer backed by application "
            "services, authentication, and a primary database. Optional components "
            "cover file storage, async processing, and observability."
        ),
        "flow": [
            "User interacts with the web client.",
            "Client sends requests to the API layer.",
            "API validates authentication and forwards to application services.",
            "Application services read and write data in the database.",
            "Optional object storage handles uploaded files.",
            "Optional background workers process async jobs.",
            "Monitoring and logging capture operational signals.",
        ],
    },
    "diagrams": {
        "high_level": {
            "title": "High Level Design",
            "nodes": [
                {"id": "user", "name": "End User", "group": "experience"},
                {"id": "web_client", "name": "Web Client", "group": "experience"},
                {"id": "api_layer", "name": "API Layer", "group": "platform"},
                {"id": "auth", "name": "Authentication Service", "group": "platform"},
                {"id": "app_service", "name": "Application Service", "group": "platform"},
                {"id": "database", "name": "Database", "group": "data"},
                {"id": "object_storage", "name": "File Storage", "group": "data"},
            ],
            "edges": [
                {"source": "user", "target": "web_client"},
                {"source": "web_client", "target": "api_layer"},
                {"source": "api_layer", "target": "auth"},
                {"source": "api_layer", "target": "app_service"},
                {"source": "app_service", "target": "database"},
                {"source": "app_service", "target": "object_storage"},
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
                {"id": "database", "name": "Database"},
                {"id": "dashboard", "name": "View Dashboard"},
            ],
            "edges": [
                {"source": "user", "target": "sign_in"},
                {"source": "sign_in", "target": "web_client"},
                {"source": "web_client", "target": "upload", "label": "optional"},
                {"source": "upload", "target": "object_storage"},
                {"source": "web_client", "target": "process"},
                {"source": "process", "target": "database"},
                {"source": "database", "target": "dashboard"},
            ],
        },
        "technical_architecture": {
            "title": "Technical Architecture",
            "nodes": [
                {"id": "user", "name": "End User", "group": "experience"},
                {"id": "web_client", "name": "Web Client", "group": "experience"},
                {"id": "api_layer", "name": "API Layer", "group": "platform"},
                {"id": "auth", "name": "Authentication Service", "group": "platform"},
                {"id": "app_service", "name": "Application Service", "group": "platform"},
                {"id": "database", "name": "Database", "group": "data"},
                {"id": "object_storage", "name": "File Storage", "group": "data"},
                {"id": "monitoring", "name": "Monitoring", "group": "operations", "type": "monitoring"},
                {"id": "logging", "name": "Logging", "group": "operations", "type": "logging"},
                {"id": "secrets", "name": "Secrets Manager", "group": "operations", "type": "secrets"},
            ],
            "edges": [
                {"source": "user", "target": "web_client"},
                {"source": "web_client", "target": "api_layer"},
                {"source": "api_layer", "target": "auth"},
                {"source": "api_layer", "target": "app_service"},
                {"source": "app_service", "target": "database"},
                {"source": "app_service", "target": "object_storage"},
                {"source": "api_layer", "target": "monitoring"},
                {"source": "app_service", "target": "logging"},
                {"source": "app_service", "target": "secrets"},
            ],
        },
    },
}
