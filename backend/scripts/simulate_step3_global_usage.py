"""Simulation harness for Step 3 (global usage model).

Runs the Step 3 flow with in-memory mappings/pricing metadata. Static values are
resolved from project input; only behavioral parameters are sent to OpenAI.

Run from the backend directory (reads OPENAI_API_KEY from .env):

    python scripts/simulate_step3_global_usage.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.clients.ai_client import AIClientFactory
from app.core.exceptions import AIClientError, AIValidationError
from app.schemas.global_usage_model import GlobalUsageModelPayload
from app.services.global_usage_model_service import GlobalUsageModelService
from app.services.static_usage_value_resolver import StaticUsageValueResolver
from app.services.usage_parameter_resolver import UsageParameterResolver

EXPECTED_USERS = 1000
STAGE = "mvp"
REQUIREMENTS = {
    "authentication": {"enabled": True},
    "file_uploads": {"enabled": False},
    "background_processing": {"enabled": False},
    "ai_usage": {"enabled": False},
}


class InMemoryMappingRepository:
    MAPPINGS = {
        "compute": {
            "category_id": "compute",
            "providers": {
                "aws": [{"service_id": "aws_lambda", "priority": 1}],
            },
        },
        "api": {
            "category_id": "api",
            "providers": {
                "aws": [{"service_id": "aws_api_gateway", "priority": 1}],
            },
        },
    }

    def find_by_id(self, category_id: str):
        return self.MAPPINGS.get(category_id)


class InMemoryPricingRepository:
    SERVICES = {
        "aws_lambda": {
            "service_id": "aws_lambda",
            "to_know": {
                "static": ["users"],
                "llm": ["requests_per_user_per_month", "average_execution_time_ms"],
            },
        },
        "aws_api_gateway": {
            "service_id": "aws_api_gateway",
            "to_know": {
                "static": ["requests_per_month"],
                "llm": ["api_requests_per_user_per_month"],
            },
        },
    }

    def find_by_id(self, service_id: str):
        return self.SERVICES.get(service_id)


SELECTED_COMPONENTS = [
    {
        "category_id": "compute",
        "name": "Compute",
        "description": "Runs application code, APIs, and background jobs.",
        "reason": "Needed to serve APIs and business logic.",
    },
    {
        "category_id": "api",
        "name": "API Gateway",
        "description": "Secure API entry point.",
        "reason": "Clients call backend APIs through a gateway.",
    },
]


def _derive_totals(payload: GlobalUsageModelPayload) -> dict[str, Any]:
    derived: dict[str, Any] = {}
    users = payload.static.get("users")
    if users is None:
        return derived

    if "api_requests_per_user_per_month" in payload.llm:
        per_user = payload.llm["api_requests_per_user_per_month"].value
        derived["requests_per_month"] = {
            "value": users * per_user,
            "formula": "users * api_requests_per_user_per_month",
        }
    return derived


def main() -> int:
    print("=" * 78)
    print("STEP 3 SIMULATION - global usage model")
    print("=" * 78)

    resolver = UsageParameterResolver(
        InMemoryMappingRepository(),
        InMemoryPricingRepository(),
    )
    resolved = resolver.resolve_for_selected_components(SELECTED_COMPONENTS)
    print(f"Resolved LLM parameters: {resolved.llm}")
    print(f"Resolved static parameters: {resolved.static}")

    static_values = StaticUsageValueResolver().resolve(
        resolved.static,
        expected_users=EXPECTED_USERS,
        stage=STAGE,
        requirements=REQUIREMENTS,
    )
    print("Static values (from project input, not sent to OpenAI):")
    for name, value in sorted(static_values.items()):
        print(f"  {name}: {value}")

    llm_usage: dict[str, Any] = {}
    if resolved.llm:
        try:
            ai_client = AIClientFactory.create()
        except AIClientError as error:
            print(f"FATAL: could not create AI client: {error}")
            return 2
        print(f"AI client: {type(ai_client).__name__}")

        service = GlobalUsageModelService(ai_client)
        started = time.perf_counter()
        try:
            llm_estimate = service.estimate(
                application_description=(
                    "A simple team task-management SaaS. Users sign in, create projects "
                    "and tasks, assign them to teammates, and track status on a board."
                ),
                platform="web",
                stage=STAGE,
                expected_users=EXPECTED_USERS,
                requirements=REQUIREMENTS,
                selected_components=SELECTED_COMPONENTS,
                usage_parameters=resolved.llm,
            )
        except AIValidationError as error:
            elapsed = time.perf_counter() - started
            print(f"HARD VALIDATION FAILED after {elapsed:.1f}s: {error.message}")
            return 1
        except AIClientError as error:
            elapsed = time.perf_counter() - started
            print(f"AI CLIENT ERROR after {elapsed:.1f}s: {error}")
            return 2

        elapsed = time.perf_counter() - started
        print(f"LLM validation passed in {elapsed:.1f}s")
        print("LLM behavioral estimates:")
        for parameter, estimate in sorted(llm_estimate.result.usage.items()):
            print(f"  {parameter}: {estimate.value} — {estimate.reason}")
        llm_usage = llm_estimate.result.usage

    payload = GlobalUsageModelPayload(llm=llm_usage, static=static_values)
    print("Combined usage model:")
    print(f"  llm keys: {sorted(payload.llm.keys())}")
    print(f"  static keys: {sorted(payload.static.keys())}")

    derived = _derive_totals(payload)
    if derived:
        print("Derived monthly totals (computed later by pricing, not sent to OpenAI):")
        for name, info in sorted(derived.items()):
            print(f"  {name}: {info['value']} ({info['formula']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
