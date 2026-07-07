"""Sample shared LLM usage-assumption responses for tests."""

from __future__ import annotations

import json


def shared_usage_assumptions_json(
    *,
    web_component_id: str = "web_client",
    api_component_id: str = "api_gateway",
    storage_component_id: str = "object_storage",
) -> str:
    payload = {
        "components": [
            {
                "component_id": web_component_id,
                "assumptions": [
                    {
                        "key": "sessions_per_user_per_month",
                        "value": 20,
                        "unit": "sessions/user/month",
                        "confidence": "medium",
                        "reasoning": "Users check tasks several times per week.",
                    },
                    {
                        "key": "requests_per_session",
                        "value": 12,
                        "unit": "requests/session",
                        "confidence": "medium",
                        "reasoning": "Each session loads lists and saves a few updates.",
                    },
                    {
                        "key": "avg_response_size_kb",
                        "value": 4,
                        "unit": "KB/request",
                        "confidence": "low",
                        "reasoning": "Mostly small JSON payloads.",
                    },
                    {
                        "key": "build_minutes_per_month",
                        "value": 20,
                        "unit": "minutes/month",
                        "confidence": "high",
                        "reasoning": "Weekly frontend deploys at MVP scale.",
                    },
                ],
            },
            {
                "component_id": api_component_id,
                "assumptions": [
                    {
                        "key": "sessions_per_user_per_month",
                        "value": 20,
                        "unit": "sessions/user/month",
                        "confidence": "medium",
                        "reasoning": "Same engagement as the web client.",
                    },
                    {
                        "key": "invocations_per_session",
                        "value": 12,
                        "unit": "invocations/session",
                        "confidence": "medium",
                        "reasoning": "One backend call per client request on average.",
                    },
                    {
                        "key": "avg_response_size_kb",
                        "value": 4,
                        "unit": "KB/invocation",
                        "confidence": "low",
                        "reasoning": "Compact API responses.",
                    },
                    {
                        "key": "plan",
                        "value": "consumption",
                        "unit": "enum",
                        "confidence": "high",
                        "reasoning": "Serverless API fits MVP traffic.",
                    },
                    {
                        "key": "avg_execution_duration_ms",
                        "value": 180,
                        "unit": "milliseconds",
                        "confidence": "medium",
                        "reasoning": "Simple CRUD handlers.",
                    },
                    {
                        "key": "memory_mb",
                        "value": 512,
                        "unit": "MB",
                        "confidence": "high",
                        "reasoning": "Default serverless memory.",
                    },
                ],
            },
            {
                "component_id": storage_component_id,
                "storage_model": {
                    "categories": [
                        {
                            "category": "user_uploads",
                            "scaling": "per_user",
                            "storage_gb_per_user": 1.0,
                            "writes_per_user_per_month": 2,
                            "reads_per_user_per_month": 4,
                            "average_object_size_kb": 512,
                            "reasoning": "Occasional file attachments per active user.",
                        }
                    ]
                },
                "assumptions": [
                    {
                        "key": "access_tier",
                        "value": "Hot",
                        "unit": "enum",
                        "confidence": "high",
                        "reasoning": "Recent uploads accessed frequently.",
                    },
                    {
                        "key": "redundancy",
                        "value": "LRS",
                        "unit": "enum",
                        "confidence": "high",
                        "reasoning": "MVP does not need geo-redundant storage.",
                    },
                ],
            },
        ]
    }
    return json.dumps(payload)
