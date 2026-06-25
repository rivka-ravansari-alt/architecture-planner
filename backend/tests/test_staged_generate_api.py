"""API integration tests for staged architecture generation."""

from __future__ import annotations

from tests.test_generate_api import _create_project


def _components_payload_from_response(components):
    return {
        "components": [
            {
                "key": component["key"],
                "name": component["name"],
                "type": component["type"],
                "reason": component["reason"],
                "optional": component["optional"],
                "cloud_mapping": component.get("cloud_mapping")
                or {"aws": [], "gcp": [], "azure": []},
                "implementation_options": component.get("implementation_options"),
            }
            for component in components
        ]
    }


def test_staged_generation_flow(api_client, mock_ai_success):
    project_id = _create_project(api_client)
    draft = api_client.post(f"/api/projects/{project_id}/generate-components")
    assert draft.status_code == 200
    body = draft.json()
    assert body["workflow_status"] == "COMPONENTS_GENERATED"
    assert len(body["components"]) == 4
    assert not body["architecture_summary"]
    assert body["architecture_diagrams"] is None
    assert not body["cost_estimates"]

    approved = api_client.put(
        f"/api/projects/{project_id}/components",
        json=_components_payload_from_response(body["components"]),
    )
    assert approved.status_code == 200
    assert approved.json()["workflow_status"] == "COMPONENTS_APPROVED"

    diagrams = api_client.post(f"/api/projects/{project_id}/generate-diagrams")
    assert diagrams.status_code == 200
    diagram_body = diagrams.json()
    assert diagram_body["workflow_status"] == "DIAGRAMS_GENERATED"
    assert diagram_body["architecture_summary"]
    assert diagram_body["architecture_diagrams"]["high_level"]["title"] == "High Level Design"
    assert not diagram_body["cost_estimates"]

    architecture = api_client.post(f"/api/projects/{project_id}/approve-architecture")
    assert architecture.status_code == 200
    assert architecture.json()["workflow_status"] == "ARCHITECTURE_APPROVED"

    pricing = api_client.post(f"/api/projects/{project_id}/generate-pricing")
    assert pricing.status_code == 200
    pricing_body = pricing.json()
    assert pricing_body["workflow_status"] == "PRICING_GENERATED"
    assert pricing_body["cost_estimates"]
    assert pricing_body["generated_at"]


def test_generate_diagrams_requires_approved_components(api_client, mock_ai_success):
    project_id = _create_project(api_client)
    api_client.post(f"/api/projects/{project_id}/generate-components")

    response = api_client.post(f"/api/projects/{project_id}/generate-diagrams")
    assert response.status_code == 400


def test_generate_pricing_requires_architecture_approval(api_client, mock_ai_success):
    project_id = _create_project(api_client)
    generated = api_client.post(f"/api/projects/{project_id}/generate-components").json()
    api_client.put(
        f"/api/projects/{project_id}/components",
        json=_components_payload_from_response(generated["components"]),
    )
    api_client.post(f"/api/projects/{project_id}/generate-diagrams")

    response = api_client.post(f"/api/projects/{project_id}/generate-pricing")
    assert response.status_code == 400


def test_skip_architecture_allows_pricing_without_diagrams(api_client, mock_ai_success):
    project_id = _create_project(api_client)
    generated = api_client.post(f"/api/projects/{project_id}/generate-components").json()
    api_client.put(
        f"/api/projects/{project_id}/components",
        json=_components_payload_from_response(generated["components"]),
    )

    skipped = api_client.post(f"/api/projects/{project_id}/skip-architecture")
    assert skipped.status_code == 200
    assert skipped.json()["workflow_status"] == "ARCHITECTURE_APPROVED"
    assert skipped.json()["architecture_diagrams"] is None

    pricing = api_client.post(f"/api/projects/{project_id}/generate-pricing")
    assert pricing.status_code == 200
    assert pricing.json()["workflow_status"] == "PRICING_GENERATED"
    assert pricing.json()["cost_estimates"]
