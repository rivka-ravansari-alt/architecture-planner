import json

from app.services.component_mapper_service import ComponentMapperService
from app.validators.ai_response_validator import AIResponseValidator
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_maps_components_with_keys():
    validated = AIResponseValidator().validate(VALID_AI_RESPONSE_JSON)
    components, risks, recs, steps, summary, flow = ComponentMapperService().map_payload(
        validated
    )
    assert len(components) == 4
    assert components[0].key
    assert components[0].cloud["aws"]


def test_feature_flags_from_required_components():
    validated = AIResponseValidator().validate(VALID_AI_RESPONSE_JSON)
    components, *_ = ComponentMapperService().map_payload(validated)
    flags = ComponentMapperService().feature_flags_from_components(components)
    assert "file_upload" in flags
    assert "ai" in flags
