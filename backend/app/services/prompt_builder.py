"""Build the architecture generation prompt from project inputs."""

from __future__ import annotations

from .. import models

_STAGE_LABELS = {"mvp": "MVP", "production": "Production"}

_PROJECT_TYPE_LABELS = {
    "web_app": "Web App",
    "mobile_app": "Mobile App",
    "chrome_extension": "Chrome Extension",
}

_EXPECTED_USERS_LABELS = {
    "100": "Up to 100",
    "1000": "Up to 1,000",
    "10000": "Up to 10,000",
    "100000+": "100,000+",
}

_REQUIREMENT_LABELS = {
    "auth": "Authentication",
    "file_upload": "File uploads",
    "background_processing": "Background processing",
    "dashboards": "Dashboards / reports",
    "ai": "AI usage",
    "payments": "Payments",
    "include_edge_cases": "Edge cases (rate limiting, backups, third-party outages)",
}


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def build_generation_prompt(project: models.Project) -> str:
    answers = project.answers
    answers_dict = {
        "auth": answers.auth if answers else False,
        "file_upload": answers.file_upload if answers else False,
        "background_processing": answers.background_processing if answers else False,
        "dashboards": answers.dashboards if answers else False,
        "ai": answers.ai if answers else False,
        "payments": answers.payments if answers else False,
        "include_edge_cases": answers.include_edge_cases if answers else False,
    }

    type_labels = [
        _PROJECT_TYPE_LABELS.get(t, t.replace("_", " ").title())
        for t in (project.project_types or [])
    ]

    requirement_lines = [
        f"- {_REQUIREMENT_LABELS[key]}: {_yes_no(value)}"
        for key, value in answers_dict.items()
    ]

    return f"""You are a senior software architect. Design a technology-agnostic architecture plan for the product described below.

Respond with JSON only. Do not include markdown, code fences, or any text outside the JSON object.

## Product

- Product name: {project.name}
- Product description: {project.description or "(not provided)"}
- Project type(s): {", ".join(type_labels)}
- Stage: {_STAGE_LABELS.get(project.stage, project.stage)}
- Expected users: {_EXPECTED_USERS_LABELS.get(project.expected_users, project.expected_users)}

## Requirements

{chr(10).join(requirement_lines)}

## Instructions

1. Propose concrete architecture components that fit the product, stage, and requirements.
2. Assign each component a type from this list only (do not invent icons or other visual metadata):
   user, web_app, mobile_app, browser_extension, api, authentication, database, object_storage, queue, worker, ai_service, monitoring, analytics, notification, payment
3. Mark each component tag as "required" or "optional".
4. Explain why each component is needed in the reason field.
5. For each component, include cloud_options with keys aws, gcp, and azure — each must be a non-empty array of concrete service names. For type "user", use "N/A — not a managed cloud service" on every provider. Never leave a provider list empty.
6. Provide a high-level architecture summary and a step-by-step flow.
7. Provide three complementary diagrams under diagrams — each with title, nodes, and edges. Node ids must be unique within each diagram. Prefer matching component names where applicable; diagrams may include process-step nodes (e.g. "Upload Document", "Validation") that describe actions rather than infrastructure components. Each diagram type has a distinct purpose and layout — do not copy the same topology with different titles.
   - high_level (title: "High Level Design"): Business and system-boundary view for non-technical stakeholders. Readable in under 30 seconds. Show major components, domains, and relationships — NOT infrastructure layering. Organize by logical domains/subsystems (e.g. User Experience, Core Platform, Data & Content). Avoid forcing all databases/storage into a bottom layer. Optional node field "group" with values: experience, platform, data, operations — to assign domain containers. Focus on the overall architecture story, not technical accuracy.
   - system_flow (title: "System Flow"): Request and data movement through the system. Use a top-to-bottom flow showing user actions, business workflow steps, and how data moves from trigger to outcome. Mostly linear vertical flow.
   - technical_flow (title: "Technical Flow"): Internal implementation detail. Use top-to-bottom flow with entry points at top and infrastructure (databases, queues, object storage, caches, workers, APIs) at the bottom. Show services, processing steps, and technical architecture.
8. Identify risks with severity low, medium, or high.
9. Provide actionable recommendations and next steps.

## Required JSON shape

{{
  "components": [
    {{
      "name": "Component name",
      "type": "database",
      "tag": "required",
      "reason": "Why this component is needed",
      "cloud_options": {{
        "aws": ["Lambda", "ECS"],
        "gcp": ["Cloud Run", "Cloud Functions"],
        "azure": ["App Service", "Functions"]
      }}
    }}
  ],
  "architecture": {{
    "summary": "High-level architecture summary",
    "flow": [
      "Step 1",
      "Step 2",
      "Step 3"
    ]
  }},
  "diagrams": {{
    "high_level": {{
      "title": "High Level Design",
      "nodes": [
        {{ "id": "user", "name": "End User", "group": "experience" }},
        {{ "id": "web_app", "name": "Web Application", "group": "experience" }},
        {{ "id": "api", "name": "API Layer", "group": "platform" }},
        {{ "id": "auth", "name": "Authentication", "group": "platform" }},
        {{ "id": "database", "name": "Primary Database", "group": "data" }},
        {{ "id": "storage", "name": "File Storage", "group": "data" }}
      ],
      "edges": [
        {{ "source": "user", "target": "web_app" }},
        {{ "source": "web_app", "target": "api" }},
        {{ "source": "api", "target": "database" }},
        {{ "source": "api", "target": "storage" }}
      ]
    }},
    "system_flow": {{
      "title": "System Flow",
      "nodes": [
        {{ "id": "user", "name": "User" }},
        {{ "id": "upload", "name": "Upload Document" }},
        {{ "id": "storage", "name": "Storage" }},
        {{ "id": "processing", "name": "Processing" }},
        {{ "id": "database", "name": "Database" }},
        {{ "id": "dashboard", "name": "Dashboard" }}
      ],
      "edges": [
        {{ "source": "user", "target": "upload" }},
        {{ "source": "upload", "target": "storage" }},
        {{ "source": "storage", "target": "processing" }},
        {{ "source": "processing", "target": "database" }},
        {{ "source": "database", "target": "dashboard" }}
      ]
    }},
    "technical_flow": {{
      "title": "Technical Flow",
      "nodes": [
        {{ "id": "browser", "name": "Browser" }},
        {{ "id": "api_gateway", "name": "API Gateway" }},
        {{ "id": "auth", "name": "Authentication" }},
        {{ "id": "app_service", "name": "Application Service" }},
        {{ "id": "queue", "name": "Queue" }},
        {{ "id": "worker", "name": "Worker" }},
        {{ "id": "validation", "name": "Validation" }},
        {{ "id": "database", "name": "Database" }}
      ],
      "edges": [
        {{ "source": "browser", "target": "api_gateway" }},
        {{ "source": "api_gateway", "target": "auth" }},
        {{ "source": "api_gateway", "target": "app_service" }},
        {{ "source": "app_service", "target": "queue" }},
        {{ "source": "queue", "target": "worker" }},
        {{ "source": "worker", "target": "validation" }},
        {{ "source": "validation", "target": "database" }}
      ]
    }}
  }},
  "risks": [
    {{
      "title": "Risk title",
      "description": "Risk description",
      "severity": "low"
    }}
  ],
  "recommendations": [
    "Recommendation 1"
  ],
  "next_steps": [
    "Next step 1"
  ]
}}
"""
