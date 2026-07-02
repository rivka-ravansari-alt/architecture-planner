import json

import pytest

from app.core.exceptions import AIValidationError
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_valid_response_passes(ai_validator):
    result = ai_validator.validate(VALID_AI_RESPONSE_JSON)
    assert len(result["components"]) == 4


def test_strips_markdown_fence(ai_validator):
    wrapped = f"```json\n{VALID_AI_RESPONSE_JSON}\n```"
    result = ai_validator.validate(wrapped)
    assert result["architecture"]["summary"]


def test_rejects_empty_response(ai_validator):
    with pytest.raises(AIValidationError, match="empty"):
        ai_validator.validate("   ")


def test_rejects_missing_components(ai_validator):
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    del payload["components"]
    with pytest.raises(AIValidationError, match="Missing required field"):
        ai_validator.validate(json.dumps(payload))


def test_preserves_diagram_group(ai_validator):
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["diagrams"]["high_level"]["nodes"][0]["group"] = "experience"
    result = ai_validator.validate(json.dumps(payload))
    assert result["diagrams"]["high_level"]["nodes"][0].get("group") == "experience"


def test_allows_node_only_diagrams(ai_validator):
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["diagrams"]["high_level"]["edges"] = []
    result = ai_validator.validate(json.dumps(payload))
    assert result["diagrams"]["high_level"]["edges"] == []


def test_normalizes_compact_ai_schema(ai_validator):
    payload = {
        "stage": "MVP",
        "components": [
            {
                "name": "Web Client",
                "type": "web_app",
                "tag": "required",
                "description": "Browser-based user interface.",
                "cloud_mappings": {
                    "aws": "Amplify Hosting",
                    "gcp": "Firebase Hosting",
                    "azure": "Static Web Apps",
                },
            }
        ],
        "architecture": {
            "summary": "A simple web architecture.",
            "flow": ["User opens the web client.", "Client calls the API."],
        },
        "diagram": {
            "title": "High Level Design",
            "nodes": [
                {"id": "client", "name": "Web Client"},
                {"id": "api", "name": "API"},
            ],
            "edges": [{"source": "client", "target": "api"}],
        },
    }
    result = ai_validator.validate(json.dumps(payload))
    assert result["components"][0]["cloud_mappings"]["aws"] == "Amplify Hosting"
    assert result["components"][0]["cloud_mappings"]["gcp"] == "Firebase Hosting"
    assert (
        result["components"][0]["reason"]
        == "Browser-based application that delivers the primary user experience."
    )
    assert "high_level" in result["diagrams"]
    assert "system_flow" in result["diagrams"]
    assert "technical_architecture" in result["diagrams"]
    assert "technical_flow" not in result["diagrams"]
