import json

from app.services.cloud_defaults_service import CloudDefaultsService
from app.validators.ai_response_validator import AIResponseValidator
from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_fills_missing_cloud_options():
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["cloud_options"] = {"aws": ["S3"]}
    validated = AIResponseValidator().validate(json.dumps(payload))
    aws = validated["components"][0]["cloud_options"]["aws"]
    gcp = validated["components"][0]["cloud_options"]["gcp"]
    assert aws
    assert gcp


def test_user_type_gets_not_applicable():
    defaults = CloudDefaultsService().default_cloud_options_for_type("user")
    assert all("N/A" in option for provider in defaults.values() for option in provider)
