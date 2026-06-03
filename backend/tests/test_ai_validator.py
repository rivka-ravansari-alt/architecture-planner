"""Tests for AI response validation."""

from __future__ import annotations

import json

import pytest

from app.services.ai_validator import AIValidationError, validate_ai_response
from tests.fixtures import VALID_AI_PAYLOAD, VALID_AI_RESPONSE_JSON


def test_accepts_valid_json_string():
    result = validate_ai_response(VALID_AI_RESPONSE_JSON)
    assert result["components"][0]["tag"] == "required"
    assert result["components"][0]["type"] == "web_app"
    assert result["architecture"]["summary"] == VALID_AI_PAYLOAD["architecture"]["summary"]


def test_accepts_json_inside_markdown_fence():
    wrapped = f"```json\n{VALID_AI_RESPONSE_JSON}\n```"
    result = validate_ai_response(wrapped)
    assert len(result["components"]) == 4


def test_normalizes_component_tag_case():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["tag"] = "REQUIRED"
    result = validate_ai_response(json.dumps(payload))
    assert result["components"][0]["tag"] == "required"


def test_normalizes_risk_severity_case():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["risks"][0]["severity"] = "HIGH"
    result = validate_ai_response(json.dumps(payload))
    assert result["risks"][0]["severity"] == "high"


@pytest.mark.parametrize(
    "raw,message",
    [
        ("", "empty"),
        ("not json at all", "JSON object"),
        (
            json.dumps(
                {
                    "components": [],
                    "architecture": {"summary": "Summary", "flow": ["Step"]},
                    "diagrams": {
                        "high_level": {
                            "title": "High Level Design",
                            "nodes": [{"id": "a", "name": "A"}],
                            "edges": [{"source": "a", "target": "a"}],
                        },
                        "system_flow": {
                            "title": "System Flow",
                            "nodes": [{"id": "b", "name": "B"}],
                            "edges": [{"source": "b", "target": "b"}],
                        },
                        "technical_flow": {
                            "title": "Technical Flow",
                            "nodes": [{"id": "c", "name": "C"}],
                            "edges": [{"source": "c", "target": "c"}],
                        },
                    },
                    "risks": [],
                    "recommendations": ["Rec"],
                    "next_steps": ["Next"],
                }
            ),
            "non-empty list",
        ),
        ('{"architecture": {}, "risks": [], "recommendations": ["x"], "next_steps": ["y"]}', "components"),
    ],
)
def test_rejects_invalid_responses(raw: str, message: str):
    with pytest.raises(AIValidationError) as exc_info:
        validate_ai_response(raw)
    assert message.lower() in str(exc_info.value).lower()


def test_rejects_invalid_component_tag():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["tag"] = "mandatory"
    with pytest.raises(AIValidationError, match="required.*optional"):
        validate_ai_response(json.dumps(payload))


def test_rejects_invalid_component_type():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["type"] = "microservice"
    with pytest.raises(AIValidationError, match="components\\[0\\].type"):
        validate_ai_response(json.dumps(payload))


def test_rejects_invalid_risk_severity():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["risks"][0]["severity"] = "critical"
    with pytest.raises(AIValidationError, match="low, medium, or high"):
        validate_ai_response(json.dumps(payload))


def test_rejects_missing_component_fields():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    del payload["components"][0]["reason"]
    with pytest.raises(AIValidationError, match="reason"):
        validate_ai_response(json.dumps(payload))


def test_fills_missing_cloud_options():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    del payload["components"][0]["cloud_options"]
    result = validate_ai_response(json.dumps(payload))
    assert result["components"][0]["cloud_options"]["aws"]
    assert result["components"][0]["cloud_options"]["gcp"]
    assert result["components"][0]["cloud_options"]["azure"]


def test_fills_empty_cloud_options_list_from_defaults():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["cloud_options"]["aws"] = []
    result = validate_ai_response(json.dumps(payload))
    assert len(result["components"][0]["cloud_options"]["aws"]) >= 1


def test_accepts_valid_diagrams():
    result = validate_ai_response(VALID_AI_RESPONSE_JSON)
    assert result["diagrams"]["high_level"]["title"] == "High Level Design"
    assert len(result["diagrams"]["high_level"]["nodes"]) == 5
    assert len(result["diagrams"]["system_flow"]["edges"]) == 5
    assert len(result["diagrams"]["technical_flow"]["nodes"]) == 6


def test_rejects_missing_diagrams():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    del payload["diagrams"]
    with pytest.raises(AIValidationError, match="diagrams"):
        validate_ai_response(json.dumps(payload))


def test_rejects_missing_diagram_key():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    del payload["diagrams"]["technical_flow"]
    with pytest.raises(AIValidationError, match="diagrams.technical_flow"):
        validate_ai_response(json.dumps(payload))


def test_rejects_diagram_edge_with_unknown_node():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["diagrams"]["high_level"]["edges"].append({"source": "missing", "target": "user"})
    with pytest.raises(AIValidationError, match="unknown node"):
        validate_ai_response(json.dumps(payload))
