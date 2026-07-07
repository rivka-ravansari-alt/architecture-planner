"""Print raw LLM usage-assumption response for Mobile Wellness App."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.clients.ai_client import AIClientFactory
from app.models import Project
from app.pricing.aws.benchmark import normalize_aws_components
from app.pricing.aws.platform_benchmark import user_count_to_project_label
from app.pricing.aws.scenarios import AWS_PLATFORM_BENCHMARK_SCENARIOS, platform_scenario_components
from app.pricing.usage.service import UsageAssumptionsService


def main() -> None:
    scenario = AWS_PLATFORM_BENCHMARK_SCENARIOS[0]
    users = 420
    components = normalize_aws_components(platform_scenario_components(scenario))
    project = Project(
        name=scenario.name,
        description=scenario.product_description,
        expected_users=user_count_to_project_label(users),
        stage=scenario.stage,
    )
    service = UsageAssumptionsService(ai_client=AIClientFactory.create(), inference_mode="llm")
    result = service.infer(
        project,
        components,
        provider="aws",
        feature_flags=scenario.feature_flags,
        inference_mode="llm",
    )

    print(f"Scenario: {scenario.name}")
    print(f"Users: {users} (band: {project.expected_users})")
    print(f"Inference source: {result.inference_source}")
    if result.audit.validation_errors:
        print(f"Validation errors: {result.audit.validation_errors}")
    print("\n=== RAW LLM RESPONSE ===\n")
    print(result.audit.raw_response or "(no raw response — likely heuristic fallback)")

    print("\n=== PARSED PER COMPONENT ===\n")
    for component in result.components:
        payload = {
            "component_id": component.component_id,
            "cloud_service": component.cloud_service,
            "behavioral": [
                {
                    "key": a.key,
                    "value": a.value,
                    "unit": a.unit,
                    "confidence": str(getattr(a.confidence, "value", a.confidence)),
                    "reasoning": a.reasoning,
                }
                for a in component.behavioral_assumptions
            ],
            "config": [
                {
                    "key": a.key,
                    "value": a.value,
                    "unit": a.unit,
                    "confidence": str(getattr(a.confidence, "value", a.confidence)),
                    "reasoning": a.reasoning,
                }
                for a in component.config_assumptions
            ],
            "resolved": [
                {"key": a.key, "value": a.value, "unit": a.unit}
                for a in component.resolved
            ],
        }
        print(json.dumps(payload, indent=2))
        print()


if __name__ == "__main__":
    main()
