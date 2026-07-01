import json

from tests.fixtures import VALID_AI_RESPONSE_JSON


def test_applies_catalog_cloud_options_by_type(ai_validator, cloud_defaults_service):
    payload = json.loads(VALID_AI_RESPONSE_JSON)
    payload["components"][0]["cloud_options"] = {"aws": ["S3"]}
    validated = ai_validator.validate(json.dumps(payload))
    component_type = validated["components"][0]["type"]
    expected = cloud_defaults_service.default_cloud_options_for_type(component_type)
    assert validated["components"][0]["cloud_options"] == expected


def test_user_type_gets_not_applicable(cloud_defaults_service):
    defaults = cloud_defaults_service.default_cloud_options_for_type("user")
    assert all("N/A" in option for provider in defaults.values() for option in provider)


def test_default_reason_for_type(cloud_defaults_service):
    assert (
        cloud_defaults_service.default_reason_for_type("web_app")
        == "Browser-based application that delivers the primary user experience."
    )
    assert (
        cloud_defaults_service.default_reason_for_type("api")
        == cloud_defaults_service.default_reason_for_type("api_gateway")
    )


def test_component_catalog_out_normalizes_structured_cloud_options():
    from app.schemas.project import ComponentCatalogOut

    entry = ComponentCatalogOut.model_validate(
        {
            "id": "1",
            "name": "web_app",
            "category": "main_architecture",
            "description": "Browser app",
            "aws_options": [{"name": "Amplify Hosting", "api_service_code": "AWSAmplify"}],
            "gcp_options": ["Firebase Hosting"],
            "azure_options": [
                {
                    "name": "Azure App Service",
                    "api_service_name": "Azure App Service",
                    "price_filter": "contains(productName, 'Static Web')",
                }
            ],
            "is_active": True,
        }
    )

    assert entry.aws_options == ["Amplify Hosting"]
    assert entry.gcp_options == ["Firebase Hosting"]
    assert entry.azure_options == ["Azure App Service"]
