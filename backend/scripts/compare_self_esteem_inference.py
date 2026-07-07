"""Compare heuristic vs LLM usage inference for the Self-Esteem benchmark."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.ai_client import AIClientFactory
from app.models import Project
from app.pricing.azure.benchmark import (
    BENCHMARK_USER_COUNTS,
    SELF_ESTEEM_PRODUCT_DESCRIPTION,
    USER_COUNT_TO_PROJECT_LABEL,
    self_esteem_scenario,
)
from app.pricing.azure.usage_inference import AzureUsageInferenceEngine
from app.pricing.azure.verification import AzurePricingVerificationRunner
from app.pricing.catalog_factory import build_azure_cost_calculator

KEY_ASSUMPTIONS = (
    "requests_per_month",
    "executions_per_month",
    "storage_gb",
    "tier",
    "queue_operations",
    "cpu",
    "memory_gb",
    "network_egress_gb",
)


def run_comparison() -> dict:
    scenario = self_esteem_scenario()
    calculator = build_azure_cost_calculator()
    heuristic_runner = AzurePricingVerificationRunner(
        calculator,
        usage_inference=AzureUsageInferenceEngine(inference_mode="heuristic"),
    )
    llm_runner = AzurePricingVerificationRunner(
        calculator,
        usage_inference=AzureUsageInferenceEngine(
            ai_client=AIClientFactory.create(),
            inference_mode="llm",
        ),
    )

    rows: list[dict] = []
    for users in BENCHMARK_USER_COUNTS:
        project = Project(
            name="Self-Esteem",
            description=SELF_ESTEEM_PRODUCT_DESCRIPTION,
            expected_users=USER_COUNT_TO_PROJECT_LABEL[users],
            stage=scenario.stage,
        )
        heuristic_report = heuristic_runner.run(
            project,
            scenario.components,
            feature_flags=scenario.feature_flags,
            inference_mode="heuristic",
        )
        llm_report = llm_runner.run(
            project,
            scenario.components,
            feature_flags=scenario.feature_flags,
            inference_mode="llm",
        )

        assumption_changes = _compare_assumptions(
            heuristic_report.components,
            llm_report.components,
        )
        rows.append(
            {
                "users": users,
                "heuristic_total": round(heuristic_report.total_usd, 2),
                "llm_total": round(llm_report.total_usd, 2),
                "difference": round(llm_report.total_usd - heuristic_report.total_usd, 2),
                "pct_change": _pct_change(heuristic_report.total_usd, llm_report.total_usd),
                "assumption_changes": assumption_changes,
                "heuristic_components": _component_summaries(heuristic_report.components),
                "llm_components": _component_summaries(llm_report.components),
            }
        )

    return {
        "scenario": "Self-Esteem App",
        "description": SELF_ESTEEM_PRODUCT_DESCRIPTION,
        "rows": rows,
    }


def _pct_change(heuristic: float, llm: float) -> float | None:
    if heuristic == 0:
        return None
    return round(((llm - heuristic) / heuristic) * 100, 1)


def _assumptions_by_component(components) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for component in components:
        result[component.architecture.component_id] = dict(component.usage_assumptions)
    return result


def _resolved_by_component(components) -> dict[str, list]:
    result: dict[str, list] = {}
    for component in components:
        result[component.architecture.component_id] = [
            {
                "key": item.key,
                "value": item.value,
                "unit": item.unit,
                "confidence": item.confidence.value if hasattr(item.confidence, "value") else item.confidence,
                "reasoning": item.reasoning,
            }
            for item in component.resolved_assumptions
        ]
    return result


def _compare_assumptions(heuristic_components, llm_components) -> list[dict]:
    heuristic = _assumptions_by_component(heuristic_components)
    llm = _assumptions_by_component(llm_components)
    changes: list[dict] = []

    for component_id in sorted(set(heuristic) | set(llm)):
        h = heuristic.get(component_id, {})
        l = llm.get(component_id, {})
        for key in sorted(set(h) | set(l)):
            if key not in KEY_ASSUMPTIONS and key not in h and key not in l:
                continue
            if key not in KEY_ASSUMPTIONS:
                continue
            old = h.get(key)
            new = l.get(key)
            if old == new:
                continue
            changes.append(
                {
                    "component": component_id,
                    "key": key,
                    "heuristic": old,
                    "llm": new,
                }
            )
    return changes


def _component_summaries(components) -> list[dict]:
    summaries: list[dict] = []
    for component in components:
        summaries.append(
            {
                "component_id": component.architecture.component_id,
                "service": component.azure_service,
                "subtotal_usd": round(component.subtotal_usd, 2),
                "usage_assumptions": component.usage_assumptions,
                "resolved_assumptions": [
                    {
                        "key": item.key,
                        "value": item.value,
                        "unit": item.unit,
                        "confidence": getattr(item.confidence, "value", item.confidence),
                        "reasoning": item.reasoning,
                    }
                    for item in component.resolved_assumptions
                ],
            }
        )
    return summaries


if __name__ == "__main__":
    report = run_comparison()
    print(json.dumps(report, indent=2))
