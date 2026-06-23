import json

from app.services.cloud_defaults_service import CloudDefaultsService
from app.validators.ai_response_validator import AIResponseValidator
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_applies_hardcoded_cloud_options_by_type():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["cloud_options"] = {"aws": ["S3"]}
    validated = AIResponseValidator().validate(json.dumps(payload))
    component_type = validated["components"][0]["type"]
    expected = CloudDefaultsService().default_cloud_options_for_type(component_type)
    assert validated["components"][0]["cloud_options"] == expected


def test_user_type_gets_not_applicable():
    defaults = CloudDefaultsService().default_cloud_options_for_type("user")
    assert all("N/A" in option for provider in defaults.values() for option in provider)


def test_default_reason_for_type():
    service = CloudDefaultsService()
    assert (
        service.default_reason_for_type("web_app")
        == "Browser-based application that delivers the primary user experience."
    )
    assert service.default_reason_for_type("api") == service.default_reason_for_type("api_gateway")
