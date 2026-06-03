"""Tests for mapping validated AI payloads to internal models."""

from __future__ import annotations

from app.services.ai_validator import validate_ai_response
from app.services.component_mapper import (
    feature_flags_from_components,
    infer_component_key,
    map_ai_payload,
)
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_infer_component_key_matches_known_names():
    assert infer_component_key("API Gateway", set()) == "api_layer"
    assert infer_component_key("Authentication Service", set()) == "auth"
    assert infer_component_key("Object Storage", set()) == "object_storage"


def test_infer_component_key_avoids_duplicates():
    used = {"api_layer"}
    assert infer_component_key("REST API Layer", used) != "api_layer"
    assert infer_component_key("REST API Layer", used).startswith("rest")


def test_map_ai_payload_sets_optional_and_cloud_mapping():
    payload = validate_ai_response(VALID_AI_RESPONSE_JSON)
    components, risks, recommendations, next_steps, summary, main_flow = map_ai_payload(payload)

    assert len(components) == 4
    assert components[0].optional is False
    assert components[0].component_type == "web_app"
    assert components[-1].optional is True
    assert components[-1].key == "object_storage"
    assert components[-1].component_type == "object_storage"
    assert components[0].cloud["aws"] == ["CloudFront", "S3"]
    assert components[2].cloud["gcp"] == ["Identity Platform", "Firebase Auth"]

    assert len(risks) == 1
    assert risks[0].severity == "high"
    assert len(recommendations) == 2
    assert len(next_steps) == 2
    assert "browser client" in summary.lower()
    assert len(main_flow) == 3


def test_feature_flags_from_required_components():
    payload = validate_ai_response(VALID_AI_RESPONSE_JSON)
    components, *_ = map_ai_payload(payload)
    flags = feature_flags_from_components(components)

    assert flags["file_upload"] is False  # object storage is optional in fixture
    assert flags["ai"] is False
    assert flags["background_processing"] is False
