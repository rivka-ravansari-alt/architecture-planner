"""Derive monthly usage volumes from user requirements and component type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config.params import STAGE_PRODUCTION
from app.schemas.domain import MappedComponent, RequirementContext

USER_COUNT_MAP: dict[str, int] = {
    "100": 100,
    "1000": 1_000,
    "10000": 10_000,
    "100000+": 100_000,
}

# Component types that do not incur direct cloud charges.
NON_BILLABLE_COMPONENT_TYPES: frozenset[str] = frozenset({"user"})

# Maps SKU roles from Firestore to usage-profile variable names for linear formulas.
ROLE_USAGE_VARIABLE: dict[str, str] = {
    "cpu": "monthly_vcpu_hours",
    "vcpu": "monthly_vcpu_hours",
    "memory": "monthly_memory_gib_hours",
    "requests": "monthly_requests",
    "read_ops": "monthly_requests",
    "write_ops": "monthly_requests",
    "duration": "monthly_gb_seconds",
    "storage": "storage_gib",
    "egress": "egress_gb",
    "execution": "monthly_executions",
    "auth_mau": "monthly_auth_events",
    "auth_events": "monthly_auth_events",
    "input_tokens": "monthly_tokens",
    "output_tokens": "monthly_tokens",
    "inference": "monthly_tokens",
    "hosting": "monthly_requests",
    "compute": "monthly_requests",
}

# Share of total API traffic attributed to each component type.
REQUEST_SHARE_BY_TYPE: dict[str, float] = {
    "web_app": 0.15,
    "mobile_app": 0.15,
    "admin_panel": 0.05,
    "browser_extension": 0.05,
    "api_gateway": 0.35,
    "api": 0.35,
    "app_service": 0.30,
    "service": 0.30,
    "auth": 0.10,
    "authentication": 0.10,
    "database": 0.05,
    "object_storage": 0.02,
    "queue": 0.08,
    "worker": 0.08,
    "queue_worker": 0.08,
    "cache": 0.03,
    "search": 0.05,
    "ai_service": 0.05,
    "ai_provider": 0.05,
    "cdn": 0.20,
    "load_balancer": 0.10,
    "monitoring": 0.01,
    "logging": 0.01,
    "tracing": 0.01,
    "alerting": 0.01,
    "notification": 0.02,
    "push_notifications": 0.02,
    "analytics": 0.03,
    "payment": 0.02,
    "payments": 0.02,
    "external_api": 0.02,
    "integration": 0.02,
    "integrations": 0.02,
    "secrets": 0.01,
    "config": 0.01,
    "backup": 0.01,
}

DEFAULT_REQUEST_SHARE = 0.05


@dataclass(frozen=True)
class UsageProfile:
    """Numeric usage variables consumed by pricing formulas."""

    values: dict[str, float]
    assumptions: dict[str, Any]
    missing_defaults: list[str]


class UsageProfileBuilder:
    def build(
        self,
        *,
        component: MappedComponent,
        expected_users: str,
        stage: str,
        requirements: RequirementContext,
    ) -> UsageProfile:
        users = USER_COUNT_MAP.get(expected_users, 1_000)
        is_production = stage == STAGE_PRODUCTION
        missing_defaults: list[str] = []

        requests_per_user = 120 if is_production else 40
        sessions_per_user = 20 if is_production else 8
        avg_request_duration = 0.35 if is_production else 0.15
        cpu = 0.5 if is_production else 0.25
        memory_gib = 1.0 if is_production else 0.5

        share = REQUEST_SHARE_BY_TYPE.get(component.component_type, DEFAULT_REQUEST_SHARE)
        monthly_requests = users * requests_per_user * share

        monthly_vcpu_hours = monthly_requests * avg_request_duration / 3600 * cpu
        monthly_memory_gib_hours = monthly_requests * avg_request_duration / 3600 * memory_gib
        monthly_gb_seconds = monthly_requests * avg_request_duration * memory_gib
        monthly_executions = monthly_requests * 0.2

        storage_per_user_gib = 0.05
        if requirements.file_upload or component.component_type in {
            "object_storage",
        }:
            storage_per_user_gib = 0.5 if is_production else 0.25
        storage_gib = users * storage_per_user_gib

        page_views_per_user = 30 if is_production else 12
        egress_gb = users * page_views_per_user * 0.002

        monthly_auth_events = users * sessions_per_user if requirements.auth else 0.0
        monthly_ai_requests = users * (10 if is_production else 3) if requirements.ai else 0.0
        monthly_tokens = monthly_ai_requests * 2_000

        if requirements.background_processing:
            monthly_executions = max(monthly_executions, users * (8 if is_production else 3))

        values: dict[str, float] = {
            "monthly_requests": monthly_requests,
            "avg_request_duration": avg_request_duration,
            "cpu": cpu,
            "memory_gib": memory_gib,
            "monthly_vcpu_hours": monthly_vcpu_hours,
            "monthly_memory_gib_hours": monthly_memory_gib_hours,
            "monthly_gb_seconds": monthly_gb_seconds,
            "monthly_executions": monthly_executions,
            "storage_gib": storage_gib,
            "egress_gb": egress_gb,
            "monthly_auth_events": monthly_auth_events,
            "monthly_ai_requests": monthly_ai_requests,
            "monthly_tokens": monthly_tokens,
        }

        for role, variable in ROLE_USAGE_VARIABLE.items():
            if role not in values and variable in values:
                values[role] = values[variable]

        assumptions: dict[str, Any] = {
            "expected_users": expected_users,
            "user_count": users,
            "stage": stage,
            "requests_per_user_per_month": requests_per_user,
            "request_share_for_component": share,
            "avg_request_duration_seconds": avg_request_duration,
            "cpu_vcpu": cpu,
            "memory_gib": memory_gib,
            "storage_per_user_gib": storage_per_user_gib,
        }

        if not requirements.file_upload and component.component_type == "object_storage":
            missing_defaults.append(
                "file_upload not enabled; using minimal storage footprint (50 MB/user)"
            )

        return UsageProfile(
            values=values,
            assumptions=assumptions,
            missing_defaults=missing_defaults,
        )

    def scale_profile(self, profile: UsageProfile, factor: float) -> UsageProfile:
        scaled = {key: value * factor for key, value in profile.values.items()}
        return UsageProfile(
            values=scaled,
            assumptions=dict(profile.assumptions),
            missing_defaults=list(profile.missing_defaults),
        )
