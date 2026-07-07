"""Derive AWS usage inputs from project scale, architecture, and feature flags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config.params import STAGE_PRODUCTION
from app.models import Project
from app.schemas.domain import MappedComponent

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


class AwsUsageModelBuilder:
    """Build per-component AWS usage assumption dicts from architecture semantics."""

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
        aws_service: str,
    ) -> dict[str, Any]:
        """Return usage input dict for one component and AWS service."""
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
            return self._service_usage(aws_service, monthly_requests, egress_gb, weight)

        if component.component_type in {"worker", "queue_worker"}:
            return self._worker_usage(aws_service, worker_jobs, egress_gb, weight)

        if component.component_type == "database":
            if "DynamoDB" in aws_service:
                return {
                    "billing_mode": "on_demand",
                    "storage_gb": max(1.0, storage_gb),
                    "read_requests_per_month": int(monthly_requests * 2 * weight),
                    "write_requests_per_month": int(monthly_requests * 0.5 * weight),
                }
            return {
                "instance_class": "db.t3.micro",
                "storage_gb": max(20, storage_gb),
                "backup_storage_gb": round(max(0, storage_gb * 0.1), 2),
                "hours_per_month": 730,
            }

        if component.component_type == "object_storage":
            if not profile.file_upload:
                return {
                    "storage_gb": round(5 * weight, 2),
                    "storage_class": "Standard",
                    "write_operations": int(1_000 * weight),
                    "read_operations": int(5_000 * weight),
                    "data_egress_gb": round(egress_gb * 0.5, 2),
                }
            return {
                "storage_gb": max(10, storage_gb),
                "storage_class": "Standard",
                "write_operations": int(monthly_requests * 0.05 * weight),
                "read_operations": int(monthly_requests * 0.2 * weight),
                "data_egress_gb": round(egress_gb * 0.5, 2),
            }

        if component.component_type == "queue":
            queue_ops = int(
                worker_jobs
                * self._defaults["queue_ops_per_worker_job"]
                * (1.5 if profile.background_processing else 1.0)
            )
            return {
                "queue_type": "Standard",
                "queue_operations": max(0, queue_ops),
                "data_egress_gb": round(egress_gb * 0.1, 2),
            }

        if component.component_type == "api_gateway":
            return {
                "requests_per_month": max(0, monthly_requests),
                "data_egress_gb": egress_gb,
                "api_type": "HTTP",
            }

        if component.component_type == "cdn":
            cdn_requests = int(monthly_requests * 3 * weight)
            return {
                "requests_per_month": max(0, cdn_requests),
                "data_transfer_gb": round(egress_gb * 1.5, 2),
            }

        if component.component_type == "load_balancer":
            lcu_hours = max(10.0, round(monthly_requests / 10_000.0, 2))
            return {
                "hours_per_month": 730,
                "lcu_hours_per_month": lcu_hours,
                "data_egress_gb": egress_gb,
            }

        if component.component_type in {"notification", "alerting"}:
            if "SES" in aws_service:
                emails = int(
                    profile.monthly_active_users
                    * (5 if component.component_type == "notification" else 1)
                    * profile.stage_factor
                    * weight
                )
                return {
                    "emails_per_month": max(0, emails),
                    "data_egress_gb": round(egress_gb * 0.02, 2),
                }
            if "CloudWatch Alarms" in aws_service or aws_service == "CloudWatch Alarms":
                alarms = max(1, profile.service_component_count)
                return {
                    "standard_alarms_count": alarms,
                    "alarm_evaluations_per_month": int(alarms * 730 * 60),
                }
            messages = int(
                profile.monthly_active_users
                * (5 if component.component_type == "notification" else 1)
                * profile.stage_factor
                * weight
            )
            return {
                "messages_per_month": max(0, messages),
                "data_egress_gb": round(egress_gb * 0.05, 2),
            }

        if component.component_type == "secrets":
            if "SSM" in aws_service:
                return {
                    "parameters_count": max(10, profile.service_component_count * 3),
                    "api_calls_per_month": int(monthly_requests * 0.05 * weight),
                }
            return {
                "secrets_count": max(3, profile.service_component_count + 2),
                "api_calls_per_month": int(monthly_requests * 0.1 * weight),
            }

        if component.component_type == "config":
            if "AppConfig" in aws_service:
                return {
                    "configurations_count": max(2, profile.service_component_count),
                    "deployment_events_per_month": max(4, profile.service_component_count * 2),
                }
            return {
                "parameters_count": max(10, profile.service_component_count * 5),
                "api_calls_per_month": int(monthly_requests * 0.2 * weight),
            }

        if component.component_type in {"mobile_app", "web_app", "admin_panel"}:
            hosting_requests = int(monthly_requests * (2 if component.component_type == "web_app" else 1))
            return {
                "hosting_requests_per_month": max(0, hosting_requests),
                "build_minutes_per_month": round(30 * weight, 1),
                "data_transfer_gb": round(egress_gb * 0.8, 2),
            }

        if component.component_type == "cache":
            return {
                "node_type": "cache.t3.micro",
                "hours_per_month": 730,
                "data_egress_gb": round(egress_gb * 0.05, 2),
            }

        if component.component_type == "search":
            return {
                "instance_hours_per_month": 730,
                "storage_gb": max(5.0, storage_gb * 0.2),
                "data_egress_gb": round(egress_gb * 0.1, 2),
            }

        if component.component_type == "ai_provider":
            ai_calls = int(
                profile.monthly_active_users
                * (10 if profile.ai else 2)
                * profile.stage_factor
                * weight
            )
            return {
                "input_tokens_per_month": ai_calls * 500,
                "output_tokens_per_month": ai_calls * 200,
            }

        if component.component_type == "analytics":
            if "QuickSight" in aws_service:
                readers = max(1, min(profile.monthly_active_users // 50, 50))
                return {"reader_seats": readers, "author_seats": max(1, profile.service_component_count)}
            if "Athena" in aws_service:
                tb = round(profile.monthly_active_users * 0.0001 * weight, 4)
                return {"data_scanned_tb_per_month": max(0.001, tb)}
            dashboards = max(1, profile.service_component_count)
            return {"dashboard_hours_per_month": dashboards * 730}

        if component.component_type == "monitoring":
            return {
                "custom_metrics_count": max(5, profile.service_component_count * 5),
                "api_requests_per_month": int(monthly_requests * 0.05 * weight),
            }

        if component.component_type == "logging":
            ingestion = round(
                profile.monthly_active_users * 0.01 * profile.stage_factor * weight,
                2,
            )
            return {
                "log_ingestion_gb_per_month": max(0.1, ingestion),
                "log_storage_gb": round(ingestion * 0.5, 2),
            }

        if component.component_type == "tracing":
            traces = int(monthly_requests * 0.1 * weight)
            return {
                "traces_ingested_per_month": max(0, traces),
                "traces_scanned_per_month": max(0, int(traces * 0.1)),
            }

        return {}

    def _service_usage(
        self,
        aws_service: str,
        monthly_requests: int,
        egress_gb: float,
        weight: float,
    ) -> dict[str, Any]:
        if "Lambda" in aws_service:
            return {
                "executions_per_month": max(0, monthly_requests),
                "avg_execution_duration_ms": 200 if weight >= 1 else 250,
                "memory_mb": 512,
                "network_egress_gb": egress_gb,
            }
        return {
            "requests_per_month": max(0, monthly_requests),
            "avg_request_duration_seconds": 0.25,
            "cpu": 0.5,
            "memory_gb": 1.0,
            "network_egress_gb": egress_gb,
            "min_tasks": 0,
        }

    def _worker_usage(
        self,
        aws_service: str,
        worker_jobs: int,
        egress_gb: float,
        weight: float,
    ) -> dict[str, Any]:
        if "Lambda" in aws_service:
            return {
                "executions_per_month": max(0, worker_jobs),
                "avg_execution_duration_ms": 400,
                "memory_mb": 512,
                "network_egress_gb": round(egress_gb * 0.3, 2),
            }
        return {
            "requests_per_month": max(0, worker_jobs),
            "avg_request_duration_seconds": 0.5,
            "cpu": 0.5,
            "memory_gb": 1.0,
            "network_egress_gb": round(egress_gb * 0.3, 2),
            "min_tasks": 0,
        }
