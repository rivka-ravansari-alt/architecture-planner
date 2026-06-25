from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_maps_components_with_keys(ai_validator, component_mapper):
    validated = ai_validator.validate(VALID_AI_RESPONSE_JSON)
    components, summary, flow = component_mapper.map_payload(validated)
    assert len(components) == 4
    assert components[0].key
    assert components[0].cloud["aws"]


def test_feature_flags_from_required_components(ai_validator, component_mapper):
    validated = ai_validator.validate(VALID_AI_RESPONSE_JSON)
    components, *_ = component_mapper.map_payload(validated)
    flags = component_mapper.feature_flags_from_components(components)
    assert "file_upload" in flags
    assert "ai" in flags
