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
