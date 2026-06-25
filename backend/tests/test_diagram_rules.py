import copy
import json

from app.services.diagram_rules_service import DiagramRulesService
from tests.fixtures import VALID_AI_PAYLOAD, VALID_AI_RESPONSE_JSON


def _diagram_rules(catalog_service) -> DiagramRulesService:
    return DiagramRulesService(
        supporting_infrastructure_types=catalog_service.supporting_infrastructure_types(),
        main_architecture_types=catalog_service.main_architecture_types(),
    )


def test_strips_supporting_infrastructure_from_high_level(ai_validator, catalog_service):
    payload = copy.deepcopy(VALID_AI_PAYLOAD)
    payload["diagrams"]["high_level"]["nodes"].extend(
        [
            {"id": "monitoring", "name": "Monitoring", "type": "monitoring"},
            {"id": "secrets", "name": "Secrets Manager", "type": "secrets"},
        ]
    )
    payload["diagrams"]["high_level"]["edges"].append(
        {"source": "api_gateway", "target": "monitoring"}
    )

    validated = ai_validator.validate(json.dumps(payload))
    result = _diagram_rules(catalog_service).apply(validated)
    node_ids = {node["id"] for node in result["diagrams"]["high_level"]["nodes"]}

    assert "monitoring" not in node_ids
    assert "secrets" not in node_ids
    assert "monitoring" in {
        node["id"] for node in result["diagrams"]["technical_architecture"]["nodes"]
    }


def test_assigns_operations_group_to_supporting_nodes_in_technical(ai_validator, catalog_service):
    payload = copy.deepcopy(VALID_AI_PAYLOAD)
    payload["diagrams"]["technical_architecture"]["nodes"].append(
        {"id": "tracing", "name": "Distributed Tracing", "type": "tracing"}
    )

    validated = ai_validator.validate(json.dumps(payload))
    result = _diagram_rules(catalog_service).apply(validated)
    tracing = next(
        node
        for node in result["diagrams"]["technical_architecture"]["nodes"]
        if node["id"] == "tracing"
    )
    assert tracing.get("group") == "operations"


def test_valid_fixture_includes_three_diagrams_after_rules(ai_validator, catalog_service):
    validated = ai_validator.validate(VALID_AI_RESPONSE_JSON)
    result = _diagram_rules(catalog_service).apply(validated)
    assert set(result["diagrams"]) == {"high_level", "system_flow", "technical_architecture"}
