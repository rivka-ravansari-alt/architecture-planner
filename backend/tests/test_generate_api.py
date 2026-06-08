"""API integration tests for architecture generation."""

from __future__ import annotations

from app.clients.ai_client import BaseAIClient
from app.core.dependencies import get_ai_client
from app.main import app


def _create_project(client) -> str:
    response = client.post(
        "/api/projects",
        json={
            "name": "API Test App",
            "description": "Testing generate endpoint",
            "project_types": ["web_app"],
            "stage": "mvp",
            "expected_users": "100",
            "answers": {
                "auth": True,
                "file_upload": False,
                "background_processing": False,
                "dashboards": False,
                "ai": False,
                "payments": False,
                "include_edge_cases": False,
            },
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_generate_endpoint_returns_ai_architecture(api_client, mock_ai_success):
    project_id = _create_project(api_client)
    response = api_client.post(f"/api/projects/{project_id}/generate")

    assert response.status_code == 200
    body = response.json()
    assert body["architecture_summary"]
    assert len(body["components"]) == 4
    assert body["cost_estimates"]
    assert body["architecture_diagrams"]["high_level"]["title"] == "High Level Design"
    assert len(body["architecture_diagrams"]["system_flow"]["nodes"]) >= 1
    assert "technical_flow" not in body["architecture_diagrams"]


def test_generate_endpoint_returns_502_on_ai_failure(api_client):
    project_id = _create_project(api_client)

    class FailingClient(BaseAIClient):
        def generate(self, prompt: str) -> str:
            raise RuntimeError("provider unavailable")

    app.dependency_overrides[get_ai_client] = lambda: FailingClient()
    try:
        response = api_client.post(f"/api/projects/{project_id}/generate")
    finally:
        app.dependency_overrides.pop(get_ai_client, None)

    assert response.status_code == 502
    assert "failed" in response.json()["detail"].lower()
