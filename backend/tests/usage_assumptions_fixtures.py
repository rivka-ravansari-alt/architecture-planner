"""Sample LLM usage-assumptions responses for tests."""

from __future__ import annotations

import json


def functions_usage_assumptions_json(
    *,
    component_id: str = "api",
    sessions_per_user_per_month: float = 24,
    invocations_per_session: float = 10,
) -> str:
    payload = {
        "components": [
            {
                "component_id": component_id,
                "assumptions": [
                    {
                        "key": "plan",
                        "value": "consumption",
                        "unit": "enum",
                        "confidence": "high",
                        "reasoning": "MVP API on serverless consumption plan.",
                    },
                    {
                        "key": "sessions_per_user_per_month",
                        "value": sessions_per_user_per_month,
                        "unit": "sessions/user/month",
                        "confidence": "medium",
                        "reasoning": "Users open the app most weekdays for task updates.",
                    },
                    {
                        "key": "invocations_per_session",
                        "value": invocations_per_session,
                        "unit": "invocations/session",
                        "confidence": "medium",
                        "reasoning": "Each session loads dashboard and saves a few tasks.",
                    },
                    {
                        "key": "avg_response_size_kb",
                        "value": 2,
                        "unit": "KB/invocation",
                        "confidence": "low",
                        "reasoning": "Small JSON payloads to web clients.",
                    },
                    {
                        "key": "avg_execution_duration_ms",
                        "value": 200,
                        "unit": "milliseconds",
                        "confidence": "medium",
                        "reasoning": "Light CRUD endpoints with minimal processing.",
                    },
                    {
                        "key": "memory_mb",
                        "value": 512,
                        "unit": "MB",
                        "confidence": "high",
                        "reasoning": "Default consumption plan memory allocation.",
                    },
                ],
            }
        ]
    }
    return json.dumps(payload)
