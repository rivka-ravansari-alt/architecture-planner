"""Tests for the OpenAI-backed global usage model service (Step 3)."""

from __future__ import annotations

import json

from app.clients.ai_client import BaseAIClient
from app.services.global_usage_model_service import GlobalUsageModelService


class MockUsageAIClient(BaseAIClient):
    def __init__(self, response: str) -> None:
        self._response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._response


def test_estimate_returns_validated_result():
    payload = {
        "usage": {
            "requests_per_user_per_month": {
                "value": 120,
                "reason": "Typical CRUD usage per active user.",
            }
        }
    }
    raw = json.dumps(payload)
    client = MockUsageAIClient(raw)
    service = GlobalUsageModelService(client)
    estimate = service.estimate(
        application_description="A team task manager.",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={},
        selected_components=[
            {
                "category_id": "compute",
                "name": "Compute",
                "description": "Runs application code.",
                "reason": "Needed for APIs.",
            }
        ],
        usage_parameters=["requests_per_user_per_month"],
    )

    assert estimate.result.usage["requests_per_user_per_month"].value == 120
    assert estimate.raw_response == raw
    assert estimate.prompt == client.last_prompt
    assert "A team task manager." in estimate.prompt


class RetryUsageAIClient(BaseAIClient):
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._responses[len(self.prompts) - 1]


def test_estimate_returns_successful_attempt_prompt_and_raw_response_after_retry():
    valid_payload = {
        "usage": {
            "requests_per_user_per_month": {
                "value": 120,
                "reason": "Typical CRUD usage per active user.",
            }
        }
    }
    client = RetryUsageAIClient(["not valid json", json.dumps(valid_payload)])
    service = GlobalUsageModelService(client, max_attempts=2)
    estimate = service.estimate(
        application_description="A team task manager.",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={},
        selected_components=[],
        usage_parameters=["requests_per_user_per_month"],
    )

    assert estimate.raw_response == json.dumps(valid_payload)
    assert estimate.prompt == client.prompts[-1]
    assert "## Correction" in estimate.prompt


def test_estimate_merges_partial_parameter_responses_across_retries():
    first_payload = {
        "usage": {
            "requests_per_user_per_month": {
                "value": 120,
                "reason": "Typical CRUD usage.",
            },
            "workload_type": {
                "value": "General Purpose",
                "reason": "Balanced web workload.",
            },
        }
    }
    second_payload = {
        "usage": {
            "required_ru_per_second": {
                "value": 400,
                "reason": "Provisioned throughput for peak reads.",
            }
        }
    }
    client = RetryUsageAIClient(
        [json.dumps(first_payload), json.dumps(second_payload)]
    )
    service = GlobalUsageModelService(client, max_attempts=3)

    estimate = service.estimate(
        application_description="A team task manager.",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={},
        selected_components=[],
        usage_parameters=[
            "requests_per_user_per_month",
            "workload_type",
            "required_ru_per_second",
        ],
    )

    assert estimate.result.usage["requests_per_user_per_month"].value == 120
    assert estimate.result.usage["workload_type"].value == "General Purpose"
    assert estimate.result.usage["required_ru_per_second"].value == 400
    assert "## Missing parameters" in client.prompts[1]
    assert "required_ru_per_second" in client.prompts[1]


def test_estimate_does_not_require_ru_per_second_for_serverless_mode():
    payload = {
        "usage": {
            "capacity_mode": {
                "value": "Serverless",
                "reason": "MVP traffic fits serverless billing.",
            },
            "request_units_per_user_per_month": {
                "value": 500,
                "reason": "Light document access.",
            },
        }
    }
    client = RetryUsageAIClient([json.dumps(payload)])
    service = GlobalUsageModelService(client, max_attempts=2)

    estimate = service.estimate(
        application_description="A notes app.",
        platform="web",
        stage="mvp",
        expected_users=1000,
        requirements={},
        selected_components=[],
        usage_parameters=[
            "capacity_mode",
            "request_units_per_user_per_month",
            "required_ru_per_second",
        ],
    )

    assert estimate.result.usage["capacity_mode"].value == "Serverless"
    assert estimate.result.usage["request_units_per_user_per_month"].value == 500
    assert estimate.result.usage["required_ru_per_second"].value == 0
    assert len(client.prompts) == 1
