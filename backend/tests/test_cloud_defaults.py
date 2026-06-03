"""Tests for cloud_options normalization."""

from __future__ import annotations

import json

from app.services.ai_validator import validate_ai_response
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_fills_empty_cloud_options_for_user_component():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"].insert(
        0,
        {
            "name": "End User",
            "type": "user",
            "tag": "required",
            "reason": "The person using the product.",
            "cloud_options": {"aws": [], "gcp": [], "azure": []},
        },
    )
    result = validate_ai_response(json.dumps(payload))
    user = result["components"][0]
    assert user["type"] == "user"
    assert len(user["cloud_options"]["aws"]) >= 1
    assert "N/A" in user["cloud_options"]["aws"][0]


def test_fills_missing_provider_keys_from_component_type_defaults():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["cloud_options"] = {
        "gcp": ["Cloud CDN"],
        "azure": ["Azure CDN"],
    }
    result = validate_ai_response(json.dumps(payload))
    aws = result["components"][0]["cloud_options"]["aws"]
    assert len(aws) >= 1
    assert any("CloudFront" in option or "Amplify" in option for option in aws)
