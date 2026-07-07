"""Derive Azure usage inputs from project scale, architecture, and feature flags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config.params import STAGE_PRODUCTION
from app.models import Project
from app.schemas.domain import MappedComponent

# Expected-users label -> approximate monthly active users.
_USER_BAND_MAU: dict[str, int] = {
    "100": 100,
    "1000": 1_000,
    "10000": 10_000,
    "100000+": 100_000,
}

_DEFAULTS = {
    "sessions_per_user_month": 30,
    "api_calls_per_session": 8,
    "worker_share_of_api_traffic": 0.35,
    "kb_per_user_storage": 64,
    "kb_per_uploaded_file": 512,
    "uploads_per_user_month": 2,
    "queue_ops_per_worker_job": 4,
    "optional_usage_factor": 0.25,
    "production_traffic_factor": 1.25,
}


@dataclass(frozen=True)
class UsageProfile:
    """Project-level traffic and storage profile for usage derivation."""

    monthly_active_users: int
    stage_factor: float
    optional_factor: float
    file_upload: bool
    background_processing: bool
    ai: bool
    service_component_count: int
    worker_component_count: int


class AzureUsageModelBuilder:
    """Build per-component Azure usage assumption dicts from architecture semantics."""

    def __init__(self, *, defaults: dict[str, Any] | None = None) -> None:
        self._defaults = defaults or _DEFAULTS

    def build_profile(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
    ) -> UsageProfile:
        flags = feature_flags or {}
        mau = _USER_BAND_MAU.get(project.expected_users, 100)
        stage_factor = (
            self._defaults["production_traffic_factor"]
            if project.stage == STAGE_PRODUCTION
            else 1.0
        )
        required_services = sum(
            1
            for c in components
            if c.component_type in {"service", "api"} and not c.optional
        )
        required_workers = sum(
            1 for c in components if c.component_type in {"worker", "queue_worker"} and not c.optional
        )
        return UsageProfile(
            monthly_active_users=mau,
            stage_factor=stage_factor,
            optional_factor=float(self._defaults["optional_usage_factor"]),
            file_upload=flags.get("file_upload", False),
            background_processing=flags.get("background_processing", False),
            ai=flags.get("ai", False),
            service_component_count=max(required_services, 1),
            worker_component_count=max(required_workers, 0),
        )

    def build_for_component(
        self,
        profile: UsageProfile,
        component: MappedComponent,
        azure_service: str,
    ) -> dict[str, Any]:
        """Return usage input dict for one component and Azure service."""
        weight = profile.optional_factor if component.optional else 1.0
        per_service_share = 1.0 / profile.service_component_count
        per_worker_share = (
            1.0 / profile.worker_component_count if profile.worker_component_count else 1.0
        )

        monthly_requests = int(
            profile.monthly_active_users
            * self._defaults["sessions_per_user_month"]
            * self._defaults["api_calls_per_session"]
            * profile.stage_factor
            * weight
            * per_service_share
        )
        monthly_executions = monthly_requests
        worker_jobs = int(
            monthly_requests * self._defaults["worker_share_of_api_traffic"] * weight * per_worker_share
        )
        egress_gb = round(
            (monthly_requests * 0.002 + worker_jobs * 0.001) * weight,
            2,
        )
        storage_gb = round(
            profile.monthly_active_users
            * (self._defaults["kb_per_user_storage"] / 1024)
            * profile.stage_factor
            * weight,
            2,
        )
        if profile.file_upload:
            storage_gb += round(
                profile.monthly_active_users
                * self._defaults["uploads_per_user_month"]
                * (self._defaults["kb_per_uploaded_file"] / 1024)
                * weight,
                2,
            )

        if component.component_type in {"service", "api"}:
            return self._service_usage(azure_service, monthly_requests, egress_gb, weight)

        if component.component_type in {"worker", "queue_worker"}:
            return self._worker_usage(azure_service, worker_jobs, egress_gb, weight)

        if component.component_type == "database":
            if "Cosmos" in azure_service:
                ru_per_user = max(50, int(profile.monthly_active_users * 0.1 * weight))
                return {
                    "request_units_per_month": max(
                        100_000,
                        int(
                            profile.monthly_active_users
                            * ru_per_user
                            * profile.stage_factor
                            * weight
                        ),
                    ),
                    "storage_gb": max(1, storage_gb),
                    "data_egress_gb": round(egress_gb * 0.1, 2),
                }
            tier = _sql_tier_for_scale(profile.monthly_active_users, storage_gb)
            return {
                "tier": tier,
                "storage_gb": max(8, storage_gb),
                "backup_storage_gb": round(max(0, storage_gb * 0.1), 2),
            }

        if component.component_type == "cdn":
            page_views = int(
                profile.monthly_active_users
                * self._defaults["sessions_per_user_month"]
                * 5
                * profile.stage_factor
                * weight
            )
            return {
                "requests_per_month": max(0, page_views),
                "data_transfer_gb": round(max(1, page_views * 0.0005) * weight, 2),
            }

        if component.component_type == "load_balancer":
            return {
                "hours_per_month": 730,
                "capacity_unit_hours": round(max(0, monthly_requests * 0.00001) * weight, 2),
                "data_egress_gb": round(egress_gb * 0.2, 2),
            }

        if component.component_type == "api_gateway":
            return {
                "requests_per_month": max(0, monthly_requests),
                "data_egress_gb": round(egress_gb * 0.15, 2),
                "sku_tier": "Consumption",
            }

        if component.component_type == "cache":
            return {
                "cache_size": "Basic C0",
                "hours_per_month": 730,
                "data_egress_gb": round(egress_gb * 0.05, 2),
            }

        if component.component_type == "search":
            return {
                "search_units_hours": 730,
                "storage_gb": max(1, round(storage_gb * 0.2, 2)),
                "data_egress_gb": round(egress_gb * 0.05, 2),
            }

        if component.component_type == "web_app" or component.component_type == "admin_panel":
            return {
                "instance_hours_per_month": 730,
                "requests_per_month": max(0, monthly_requests),
                "data_egress_gb": round(egress_gb * 0.4, 2),
            }

        if component.component_type == "mobile_app":
            return {
                "build_minutes_per_month": round(max(10, profile.monthly_active_users * 0.01) * weight, 2),
                "test_device_minutes_per_month": round(max(0, profile.monthly_active_users * 0.005) * weight, 2),
            }

        if component.component_type == "ai_provider":
            tokens_per_user = 5000 if profile.ai else 500
            return {
                "input_tokens_per_month": int(
                    profile.monthly_active_users * tokens_per_user * profile.stage_factor * weight
                ),
                "output_tokens_per_month": int(
                    profile.monthly_active_users * (tokens_per_user // 2) * profile.stage_factor * weight
                ),
            }

        if component.component_type == "notification":
            if "Voice" in azure_service:
                return {
                    "voice_minutes_per_month": round(
                        max(0, profile.monthly_active_users * 0.01) * weight, 2
                    ),
                    "sms_messages_per_month": int(profile.monthly_active_users * 0.05 * weight),
                }
            return {
                "push_notifications_per_month": int(
                    profile.monthly_active_users * 10 * profile.stage_factor * weight
                ),
                "namespace_hours_per_month": 730,
            }

        if component.component_type == "analytics":
            if "Power BI" in azure_service:
                return {
                    "pro_seats": max(1, int(3 * weight)),
                    "premium_capacity_hours": 0,
                }
            if "Application Insights" in azure_service:
                return {
                    "telemetry_gb_per_month": round(
                        max(0.1, profile.monthly_active_users * 0.002) * weight, 2
                    ),
                    "log_queries_per_month": int(profile.monthly_active_users * 0.5 * weight),
                }
            return {
                "pro_seats": max(1, int(3 * weight)),
                "premium_capacity_hours": 0,
            }

        if component.component_type == "secrets":
            return {
                "secrets_count": max(1, int(5 * weight)),
                "operations_per_month": int(monthly_requests * 0.01 * weight),
            }

        if component.component_type == "config":
            return {
                "configuration_stores": max(1, int(weight)),
                "requests_per_month": int(monthly_requests * 0.02 * weight),
            }

        if component.component_type == "monitoring" or component.component_type == "alerting":
            return {
                "metrics_count": max(0, int(profile.service_component_count * 5 * weight)),
                "alert_rules_count": max(1, int(3 * weight)),
                "api_requests_per_month": int(monthly_requests * 0.01 * weight),
            }

        if component.component_type == "logging":
            return {
                "log_ingestion_gb_per_month": round(
                    max(0.1, profile.monthly_active_users * 0.001) * weight, 2
                ),
                "log_retention_gb": round(max(0.5, storage_gb * 0.02) * weight, 2),
            }

        if component.component_type == "tracing":
            return {
                "telemetry_gb_per_month": round(
                    max(0.05, profile.monthly_active_users * 0.0005) * weight, 2
                ),
                "log_queries_per_month": int(profile.monthly_active_users * 0.2 * weight),
            }

        if component.component_type == "object_storage":
            if not profile.file_upload:
                read_ops = int(5_000 * weight)
                return {
                    "storage_gb": round(5 * weight, 2),
                    "access_tier": "Hot",
                    "redundancy": "LRS",
                    "write_operations": int(1_000 * weight),
                    "read_operations": read_ops,
                    "list_operations": max(0, int(read_ops * 0.05)),
                    "data_egress_gb": round(egress_gb * 0.5, 2),
                }
            read_ops = int(monthly_requests * 0.2 * weight)
            return {
                "storage_gb": max(10, storage_gb),
                "access_tier": "Hot",
                "redundancy": "LRS",
                "write_operations": int(monthly_requests * 0.05 * weight),
                "read_operations": read_ops,
                "list_operations": max(0, int(read_ops * 0.05)),
                "data_egress_gb": round(egress_gb * 0.5, 2),
            }

        if component.component_type == "queue":
            queue_ops = int(
                worker_jobs
                * self._defaults["queue_ops_per_worker_job"]
                * (1.5 if profile.background_processing else 1.0)
            )
            queue_egress_gb = round(max(0.01, queue_ops * 0.00001) * weight, 2)
            if "Service Bus" in azure_service:
                return {
                    "messaging_tier": "Standard",
                    "queue_operations": max(0, queue_ops),
                    "brokered_connections": max(10, int(profile.monthly_active_users * 0.01 * weight)),
                    "data_egress_gb": queue_egress_gb,
                }
            return {
                "queue_operations": max(0, queue_ops),
                "storage_gb": max(0.5, round(storage_gb * 0.05, 2)),
                "data_egress_gb": queue_egress_gb,
            }

        return {}

    def _service_usage(
        self,
        azure_service: str,
        monthly_requests: int,
        egress_gb: float,
        weight: float,
    ) -> dict[str, Any]:
        if "Functions" in azure_service:
            return {
                "executions_per_month": max(0, monthly_requests),
                "avg_execution_duration_ms": 200 if weight >= 1 else 250,
                "memory_mb": 512,
                "network_egress_gb": egress_gb,
                "plan": "consumption",
            }
        return {
            "requests_per_month": max(0, monthly_requests),
            "avg_request_duration_seconds": 0.25,
            "cpu": 0.5,
            "memory_gb": 1.0,
            "network_egress_gb": egress_gb,
            "min_replicas": 0,
            "max_replicas": 10,
        }

    def _worker_usage(
        self,
        azure_service: str,
        worker_jobs: int,
        egress_gb: float,
        weight: float,
    ) -> dict[str, Any]:
        if "Functions" in azure_service:
            return {
                "executions_per_month": max(0, worker_jobs),
                "avg_execution_duration_ms": 400,
                "memory_mb": 512,
                "network_egress_gb": round(egress_gb * 0.3, 2),
                "plan": "consumption",
            }
        return {
            "requests_per_month": max(0, worker_jobs),
            "avg_request_duration_seconds": 0.5,
            "cpu": 0.5,
            "memory_gb": 1.0,
            "network_egress_gb": round(egress_gb * 0.3, 2),
            "min_replicas": 0,
            "max_replicas": 5,
        }


def _sql_tier_for_scale(monthly_active_users: int, storage_gb: float) -> str:
    """Pick a DTU tier label that scales with project size."""
    if monthly_active_users >= 100_000 or storage_gb >= 500:
        return "Standard S4"
    if monthly_active_users >= 10_000 or storage_gb >= 100:
        return "Standard S2"
    if monthly_active_users >= 1_000 or storage_gb >= 32:
        return "Standard S1"
    if monthly_active_users >= 100:
        return "Standard S0"
    return "Basic"
