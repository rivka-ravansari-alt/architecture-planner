"""Benchmark AWS catalog pricing for the Self-Esteem scenario with LLM usage inference."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.ai_client import AIClientFactory
from app.models import Project
from app.pricing.aws.project_costing import AwsProjectCostingPipeline
from app.pricing.azure.benchmark import (
    BENCHMARK_USER_COUNTS,
    SELF_ESTEEM_PRODUCT_DESCRIPTION,
    USER_COUNT_TO_PROJECT_LABEL,
    self_esteem_scenario,
)
from app.pricing.usage.service import UsageAssumptionsService
from app.schemas.domain import MappedComponent
from app.pricing.catalog_factory import build_aws_cost_calculator

# Catalog name aliases not yet in AwsPricingModelRegistry.
_AWS_SERVICE_ALIASES = {
    "rds postgresql": "RDS",
    "rds mysql": "RDS",
}


def _aws_components(components: list[MappedComponent]) -> list[MappedComponent]:
    normalized: list[MappedComponent] = []
    for component in components:
        item = deepcopy(component)
        aws_name = str(item.cloud.get("aws", ""))
        alias = _AWS_SERVICE_ALIASES.get(aws_name.strip().casefold())
        if alias:
            item.cloud = dict(item.cloud)
            item.cloud["aws"] = alias
        normalized.append(item)
    return normalized


def run_benchmark() -> dict:
    scenario = self_esteem_scenario()
    components = _aws_components(scenario.components)
    calculator = build_aws_cost_calculator()
    from app.pricing.aws.usage_inference import AwsUsageInferenceEngine

    pipeline = AwsProjectCostingPipeline(
        AwsUsageInferenceEngine(),
        calculator,
    )

    usage_service = UsageAssumptionsService(ai_client=AIClientFactory.create())

    rows: list[dict] = []
    for users in BENCHMARK_USER_COUNTS:
        project = Project(
            name="Self-Esteem",
            description=SELF_ESTEEM_PRODUCT_DESCRIPTION,
            expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
            stage=scenario.stage,
        )
        prompt = usage_service.build_prompt(
            project,
            components,
            provider="aws",
            feature_flags=scenario.feature_flags,
        )
        raw = AIClientFactory.create().generate(prompt)
        inference = usage_service.parse_response(
            raw,
            project,
            components,
            provider="aws",
            feature_flags=scenario.feature_flags,
        )
        pricing_inputs = list(inference.components)
        result = pipeline.calculate(
            project,
            components,
            pricing_inputs=pricing_inputs,
            feature_flags=scenario.feature_flags,
        )

        component_details: list[dict] = []
        for component_input in pricing_inputs:
            resolved = [
                {
                    "key": a.key,
                    "value": a.value,
                    "unit": a.unit,
                    "confidence": getattr(a.confidence, "value", a.confidence),
                    "reasoning": a.reasoning,
                }
                for a in component_input.resolved
            ]
            behavioral = [
                {
                    "key": a.key,
                    "value": a.value,
                    "unit": a.unit,
                    "confidence": getattr(a.confidence, "value", a.confidence),
                    "reasoning": a.reasoning,
                }
                for a in component_input.behavioral_assumptions
            ]
            cost_component = next(
                (c for c in result.components if c.component_id == component_input.component_id),
                None,
            )
            component_details.append(
                {
                    "component_id": component_input.component_id,
                    "aws_service": component_input.cloud_service,
                    "subtotal_usd": round(cost_component.subtotal_usd, 2) if cost_component else 0.0,
                    "behavioral_assumptions": behavioral,
                    "resolved_assumptions": resolved,
                }
            )

        rows.append(
            {
                "users": users,
                "total_usd": round(result.total_usd, 2),
                "inference_source": inference.inference_source,
                "components": component_details,
                "warnings": result.warnings,
            }
        )

    return {
        "product": "Self-Esteem",
        "description": SELF_ESTEEM_PRODUCT_DESCRIPTION,
        "provider": "aws",
        "feature_flags": scenario.feature_flags,
        "requirements": "default (all requirement flags false)",
        "rows": rows,
    }


if __name__ == "__main__":
    report = run_benchmark()
    print(json.dumps(report, indent=2))
