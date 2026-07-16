"""Tests for resolving LLM and static usage parameters."""

from __future__ import annotations

from app.services.usage_parameter_resolver import (
    ResolvedUsageParameters,
    UsageParameterResolver,
    is_derived_total_usage_parameter,
)


class FakeMappingRepository:
    def __init__(self, mappings: dict[str, dict]) -> None:
        self._mappings = mappings

    def find_by_id(self, category_id: str):
        return self._mappings.get(category_id)


class FakePricingRepository:
    def __init__(self, services: dict[str, dict]) -> None:
        self._services = services

    def find_by_id(self, service_id: str):
        return self._services.get(service_id)


def test_resolve_parameters_groups_llm_and_static_separately():
    mappings = {
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
        "storage": {
            "category_id": "storage",
            "providers": {
                "aws": [{"service_id": "aws_s3", "priority": 1}],
            },
        },
    }
    pricing = {
        "aws_lambda": {
            "service_id": "aws_lambda",
            "to_know": {
                "static": ["users"],
                "llm": ["requests_per_user_per_month", "memory_mb"],
            },
        },
        "aws_api_gateway": {
            "service_id": "aws_api_gateway",
            "to_know": {
                "static": ["requests_per_month"],
                "llm": ["api_requests_per_user_per_month"],
            },
        },
        "aws_s3": {
            "service_id": "aws_s3",
            "to_know": {
                "static": ["documents_per_month", "average_document_size_mb"],
                "llm": ["monthly_reads_per_file"],
            },
        },
    }

    resolver = UsageParameterResolver(
        FakeMappingRepository(mappings),
        FakePricingRepository(pricing),
    )
    selected = [
        {"category_id": "compute", "name": "Compute"},
        {"category_id": "api", "name": "API Gateway"},
        {"category_id": "storage", "name": "Object Storage"},
    ]

    resolved = resolver.resolve_for_selected_components(selected)

    assert isinstance(resolved, ResolvedUsageParameters)
    assert resolved.llm == [
        "api_requests_per_user_per_month",
        "memory_mb",
        "monthly_reads_per_file",
        "requests_per_user_per_month",
    ]
    assert resolved.static == [
        "average_document_size_mb",
        "documents_per_month",
        "stage",
        "users",
    ]


def test_resolve_parameters_excludes_derived_totals_from_both_groups():
    resolver = UsageParameterResolver(
        FakeMappingRepository(
            {
                "api": {
                    "category_id": "api",
                    "providers": {
                        "aws": [{"service_id": "aws_api_gateway", "priority": 1}],
                    },
                }
            }
        ),
        FakePricingRepository(
            {
                "aws_api_gateway": {
                    "service_id": "aws_api_gateway",
                    "to_know": {
                        "static": ["users", "requests_per_month"],
                        "llm": ["requests_per_month", "api_requests_per_user_per_month"],
                    },
                }
            }
        ),
    )

    resolved = resolver.resolve_for_selected_components(
        [{"category_id": "api", "name": "API Gateway"}]
    )

    assert resolved.llm == ["api_requests_per_user_per_month"]
    assert resolved.static == ["stage", "users"]


def test_resolve_parameters_ignores_unknown_categories_and_services():
    resolver = UsageParameterResolver(
        FakeMappingRepository({}),
        FakePricingRepository({}),
    )
    selected = [{"category_id": "unknown", "name": "Unknown"}]

    resolved = resolver.resolve_for_selected_components(selected)
    assert resolved.llm == []
    assert resolved.static == ["stage", "users"]


def test_is_derived_total_usage_parameter():
    assert is_derived_total_usage_parameter("requests_per_month")
    assert is_derived_total_usage_parameter("messages_per_month")
    assert not is_derived_total_usage_parameter("api_requests_per_user_per_month")
    assert not is_derived_total_usage_parameter("users")
