"""Static architecture JSON used when OpenAI calls are disabled."""

from __future__ import annotations

STATIC_AI_PAYLOAD: dict = {
    "components": [
        {
            "name": "Web Client",
            "type": "web_app",
            "tag": "required",
            "reason": "Provides the user interface for interacting with the product.",
            "cloud_options": {
                "aws": ["CloudFront", "S3", "Amplify Hosting"],
                "gcp": ["Cloud CDN", "Cloud Storage", "Firebase Hosting"],
                "azure": ["Azure CDN", "Static Web Apps", "Blob Storage"],
            },
        },
        {
            "name": "API Layer",
            "type": "api",
            "tag": "required",
            "reason": "Central entry point for client requests and service routing.",
            "cloud_options": {
                "aws": ["API Gateway", "Application Load Balancer"],
                "gcp": ["API Gateway", "Cloud Load Balancing"],
                "azure": ["API Management", "Application Gateway"],
            },
        },
        {
            "name": "Application Service",
            "type": "worker",
            "tag": "required",
            "reason": "Runs core business logic and orchestrates backend workflows.",
            "cloud_options": {
                "aws": ["Lambda", "ECS", "Elastic Beanstalk"],
                "gcp": ["Cloud Run", "Cloud Functions", "App Engine"],
                "azure": ["App Service", "Azure Functions", "Container Apps"],
            },
        },
        {
            "name": "Authentication Service",
            "type": "authentication",
            "tag": "required",
            "reason": "Handles user sign-up, login, and session management.",
            "cloud_options": {
                "aws": ["Cognito"],
                "gcp": ["Identity Platform", "Firebase Auth"],
                "azure": ["Entra ID B2C", "Entra ID"],
            },
        },
        {
            "name": "Database",
            "type": "database",
            "tag": "required",
            "reason": "Stores application data with durable, queryable persistence.",
            "cloud_options": {
                "aws": ["RDS", "DynamoDB", "Aurora"],
                "gcp": ["Cloud SQL", "Firestore", "Spanner"],
                "azure": ["Azure SQL", "Cosmos DB", "PostgreSQL Flexible Server"],
            },
        },
        {
            "name": "Object Storage",
            "type": "object_storage",
            "tag": "optional",
            "reason": "Stores uploaded files and static assets when file uploads are needed.",
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
            "cloud_options": {
                "aws": ["SQS", "Lambda", "ECS workers"],
                "gcp": ["Pub/Sub", "Cloud Run workers", "Cloud Tasks"],
                "azure": ["Service Bus", "Azure Functions", "Container Apps jobs"],
            },
        },
        {
            "name": "Monitoring and Logging",
            "type": "monitoring",
            "tag": "optional",
            "reason": "Tracks health, metrics, and logs for production operations.",
            "cloud_options": {
                "aws": ["CloudWatch", "CloudWatch Logs"],
                "gcp": ["Cloud Monitoring", "Cloud Logging"],
                "azure": ["Azure Monitor", "Log Analytics"],
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
                {"id": "monitoring", "name": "Monitoring", "group": "operations"},
            ],
            "edges": [
                {"source": "user", "target": "web_client"},
                {"source": "web_client", "target": "api_layer"},
                {"source": "api_layer", "target": "auth"},
                {"source": "api_layer", "target": "app_service"},
                {"source": "app_service", "target": "database"},
                {"source": "app_service", "target": "object_storage"},
                {"source": "api_layer", "target": "monitoring"},
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
        "technical_flow": {
            "title": "Technical Flow",
            "nodes": [
                {"id": "browser", "name": "Browser"},
                {"id": "api_gateway", "name": "API Gateway"},
                {"id": "auth", "name": "Authentication"},
                {"id": "app_service", "name": "Application Service"},
                {"id": "queue", "name": "Processing Queue"},
                {"id": "worker", "name": "Background Worker"},
                {"id": "object_storage", "name": "Object Storage"},
                {"id": "database", "name": "Database"},
            ],
            "edges": [
                {"source": "browser", "target": "api_gateway"},
                {"source": "api_gateway", "target": "auth"},
                {"source": "api_gateway", "target": "app_service"},
                {"source": "app_service", "target": "queue"},
                {"source": "queue", "target": "worker"},
                {"source": "worker", "target": "object_storage"},
                {"source": "worker", "target": "database"},
                {"source": "app_service", "target": "database"},
            ],
        },
    },
    "risks": [
        {
            "title": "Authentication gaps",
            "description": "Weak session handling could expose user accounts.",
            "severity": "high",
        },
        {
            "title": "Database scaling",
            "description": "Traffic growth may require indexing and scaling strategy.",
            "severity": "medium",
        },
        {
            "title": "Cost overruns",
            "description": "Optional services can increase monthly spend if left always on.",
            "severity": "low",
        },
    ],
    "recommendations": [
        "Start with managed auth and database services to reduce operational overhead.",
        "Keep async processing optional until traffic justifies a queue and workers.",
        "Add monitoring before production launch.",
    ],
    "next_steps": [
        "Confirm required vs optional components with stakeholders.",
        "Pick a primary cloud provider and map services.",
        "Define MVP deployment and CI/CD pipeline.",
    ],
}
