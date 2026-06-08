import json

import pytest

from app.core.exceptions import AIValidationError
from app.validators.ai_response_validator import AIResponseValidator
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_valid_response_passes():
    result = AIResponseValidator().validate(VALID_AI_RESPONSE_JSON)
    assert len(result["components"]) == 4


def test_strips_markdown_fence():
    wrapped = f"```json\n{VALID_AI_RESPONSE_JSON}\n```"
    result = AIResponseValidator().validate(wrapped)
    assert result["architecture"]["summary"]


def test_rejects_empty_response():
    with pytest.raises(AIValidationError, match="empty"):
        AIResponseValidator().validate("   ")


def test_rejects_missing_components():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    del payload["components"]
    with pytest.raises(AIValidationError, match="Missing required field"):
        AIResponseValidator().validate(json.dumps(payload))


def test_preserves_diagram_group():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["diagrams"]["high_level"]["nodes"][0]["group"] = "experience"
    result = AIResponseValidator().validate(json.dumps(payload))
    assert result["diagrams"]["high_level"]["nodes"][0].get("group") == "experience"


def test_normalizes_compact_ai_schema():
    payload = {
        "stage": "MVP",
        "components": [
            {
                "name": "Web Client",
                "type": "web_app",
                "tag": "required",
                "description": "Browser-based user interface.",
                "cloud_mappings": {
                    "aws": ["Amplify Hosting"],
                    "gcp": ["Firebase Hosting"],
                    "azure": ["Static Web Apps"],
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
    result = AIResponseValidator().validate(json.dumps(payload))
    assert result["components"][0]["reason"] == "Browser-based user interface."
    assert result["components"][0]["cloud_options"]["aws"] == ["Amplify Hosting"]
    assert "high_level" in result["diagrams"]
    assert "system_flow" in result["diagrams"]
    assert "technical_architecture" in result["diagrams"]
    assert "technical_flow" not in result["diagrams"]
