import copy
import json

import pytest

from app.models import Project, RequirementAnswers
from app.services.architecture_guardrail_service import ArchitectureGuardrailService
from tests.fixtures import VALID_AI_PAYLOAD, VALID_AI_RESPONSE_JSON


@pytest.fixture
def small_mvp_project():
    return Project(
        name="TaskFlow",
        description="A simple task tracker.",
        project_types=["web_app"],
        stage="mvp",
        expected_users="100",
        answers=RequirementAnswers(
            auth=True,
            dashboards=False,
            ai=True,
        ),
    )


def _validate_and_apply(payload: dict, project: Project, ai_validator) -> dict:
    validated = ai_validator.validate(json.dumps(payload))
    return ArchitectureGuardrailService().apply(validated, project)


def test_demotes_required_analytics_when_dashboards_disabled(small_mvp_project, ai_validator):
    payload = copy.deepcopy(VALID_AI_PAYLOAD)
    payload["components"].append(
        {
            "name": "Analytics",
            "type": "analytics",
            "tag": "required",
            "reason": "Reporting layer.",
            "implementation_options": {
                "recommended": "managed_service",
                "serverless": {
                    "when_to_use": "Not applicable for this component.",
                    "cost_impact": "",
                    "pros": [],
                    "cons": [],
                    "not_applicable": True,
                },
                "container": {
                    "when_to_use": "Not applicable for this component.",
                    "cost_impact": "",
                    "pros": [],
                    "cons": [],
                    "not_applicable": True,
                },
                "managed_service": {
                    "when_to_use": "Managed BI tooling.",
                    "cost_impact": "Moderate monthly cost.",
                    "pros": ["Managed dashboards"],
                    "cons": ["Higher cost at small scale"],
                },
                "external_provider": {
                    "when_to_use": "Not applicable for this component.",
                    "cost_impact": "",
                    "pros": [],
                    "cons": [],
                    "not_applicable": True,
                },
            },
            "cloud_options": {
                "aws": ["QuickSight"],
                "gcp": ["Looker Studio"],
                "azure": ["Power BI"],
            },
        }
    )

    result = _validate_and_apply(payload, small_mvp_project, ai_validator)
    analytics = next(item for item in result["components"] if item["type"] == "analytics")
    assert analytics["tag"] == "optional"
    assert analytics["cloud_mappings"]["aws"] == "CloudWatch Dashboards"


def test_ignores_llm_cloud_options_and_uses_db_defaults(small_mvp_project, ai_validator):
    payload = copy.deepcopy(VALID_AI_PAYLOAD)
    payload["components"].append(
        {
            "name": "AI Provider",
            "type": "ai_service",
            "tag": "required",
            "reason": "Adds AI features to the product.",
            "implementation_options": {
                "recommended": "managed_service",
                "serverless": {
                    "when_to_use": "Not applicable for this component.",
                    "cost_impact": "",
                    "pros": [],
                    "cons": [],
                    "not_applicable": True,
                },
                "container": {
                    "when_to_use": "Not applicable for this component.",
                    "cost_impact": "",
                    "pros": [],
                    "cons": [],
                    "not_applicable": True,
                },
                "managed_service": {
                    "when_to_use": "Managed ML platform.",
                    "cost_impact": "High baseline cost.",
                    "pros": ["Full platform control"],
                    "cons": ["Expensive for MVP"],
                },
                "external_provider": {
                    "when_to_use": "Hosted LLM APIs.",
                    "cost_impact": "Usage-based pricing.",
                    "pros": ["Fast integration"],
                    "cons": ["Vendor limits"],
                },
            },
            "cloud_options": {
                "aws": ["SageMaker", "S3"],
                "gcp": ["Vertex AI"],
                "azure": ["Azure ML"],
            },
        }
    )

    result = _validate_and_apply(payload, small_mvp_project, ai_validator)
    ai_component = next(item for item in result["components"] if item["type"] == "ai_provider")
    assert ai_component["cloud_mappings"]["aws"] == "Bedrock"
    assert ai_component["cloud_mappings"]["gcp"] == "Gemini API"
    assert "implementation_options" not in ai_component


def test_uses_db_cloud_mappings(small_mvp_project, ai_validator):
    payload = copy.deepcopy(VALID_AI_PAYLOAD)
    payload["components"].append(
        {
            "name": "Database",
            "type": "database",
            "tag": "required",
            "reason": "Stores application data.",
            "implementation_options": {
                "recommended": "managed_service",
                "serverless": {
                    "when_to_use": "Serverless DB tiers for spiky MVP workloads when available.",
                    "cost_impact": "Low entry cost; can rise with storage and I/O.",
                    "pros": ["Scales with demand"],
                    "cons": ["Vendor-specific limits"],
                },
                "container": {
                    "when_to_use": "Self-managed database on containers only if strong control is required.",
                    "cost_impact": "Higher ops cost.",
                    "pros": ["Maximum control"],
                    "cons": ["High operational burden"],
                },
                "managed_service": {
                    "when_to_use": "Default — managed relational or document database.",
                    "cost_impact": "Moderate fixed cost.",
                    "pros": ["Automated backups and patches"],
                    "cons": ["Vendor lock-in for advanced features"],
                },
                "external_provider": {
                    "when_to_use": "Not applicable for this component.",
                    "cost_impact": "",
                    "pros": [],
                    "cons": [],
                    "not_applicable": True,
                },
            },
            "cloud_options": {
                "aws": ["RDS", "Aurora"],
                "gcp": ["Cloud SQL"],
                "azure": ["Azure SQL"],
            },
        }
    )

    result = _validate_and_apply(payload, small_mvp_project, ai_validator)
    normalized_db = next(item for item in result["components"] if item["type"] == "database")
    assert normalized_db["cloud_mappings"]["aws"] == "DynamoDB"
    assert normalized_db["cloud_mappings"]["gcp"] == "Cloud Firestore"


def test_existing_valid_fixture_still_passes_through_guardrails(small_mvp_project, ai_validator):
    validated = ai_validator.validate(VALID_AI_RESPONSE_JSON)
    result = ArchitectureGuardrailService().apply(validated, small_mvp_project)
    assert len(result["components"]) == 4
