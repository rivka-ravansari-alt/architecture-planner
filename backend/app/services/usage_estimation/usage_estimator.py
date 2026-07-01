"""Estimate provider-independent resource consumption from users, architecture, and usage profile."""

from __future__ import annotations

from app.config.params import STAGE_PRODUCTION, USAGE_ESTIMATION_BASE, USAGE_STAGE_PRODUCTION_MULTIPLIER
from app.schemas.domain import MappedComponent
from app.services.usage_estimation.component_usage_allocator import ComponentUsageAllocator
from app.services.usage_estimation.models import (
    ArchitectureUsageEstimate,
    ProductCapabilities,
    ResourceConsumption,
)
from app.services.usage_estimation.usage_profile import UsageProfile


from app.services.usage_estimation.usage_baseline import parse_active_user_count, resolve_hosting_instance_metrics


class UsageEstimator:
    """Estimates cloud resource consumption — no pricing knowledge."""

    def __init__(self, *, allocator: ComponentUsageAllocator | None = None) -> None:
        self._allocator = allocator or ComponentUsageAllocator()

    def estimate(
        self,
        *,
        expected_users: str,
        stage: str,
        components: list[MappedComponent],
        capabilities: ProductCapabilities | dict[str, bool] | None = None,
        usage_profile: UsageProfile | dict[str, object] | None = None,
    ) -> ArchitectureUsageEstimate:
        caps_input = (
            capabilities
            if isinstance(capabilities, ProductCapabilities)
            else ProductCapabilities.from_dict(capabilities)
        )
        if isinstance(usage_profile, UsageProfile):
            profile = usage_profile
        elif usage_profile:
            profile = UsageProfile.from_dict(usage_profile)
        else:
            profile = None

        if profile is None:
            profile = UsageProfile.build_baseline(
                expected_users=expected_users,
                capabilities=caps_input,
            )

        caps = profile.to_capabilities()
        users = profile.resolve_monthly_active_users(expected_users=expected_users)
        global_consumption = self._estimate_from_profile(
            profile=profile,
            users=users,
            stage=stage,
        )

        component_consumption = self._allocator.allocate_all(
            components,
            global_consumption,
            stage=stage,
        )
        return ArchitectureUsageEstimate(
            expected_users=expected_users,
            stage=stage,
            capabilities=caps,
            global_consumption=global_consumption,
            component_consumption=component_consumption,
        )

    def _estimate_from_profile(
        self,
        *,
        profile: UsageProfile,
        users: int,
        stage: str,
    ) -> ResourceConsumption:
        base = USAGE_ESTIMATION_BASE
        active_days = base.get("active_days_per_month", 25.0)
        actions_per_day = profile.actions_per_user_per_day()
        duration_sec = base["avg_request_duration_seconds"]
        cpu_vcpu = base["cpu_vcpu_per_request"]
        memory_gib = base["memory_gib_per_request"]

        monthly_requests = users * actions_per_day * active_days
        cpu_seconds = monthly_requests * duration_sec * cpu_vcpu
        memory_gib_seconds = monthly_requests * duration_sec * memory_gib

        storage_gb, database_storage_gb = profile.estimate_storage_gb(users=users)
        outbound_network_gb = users * base["outbound_gb_per_user"]
        database_reads = monthly_requests * base["db_reads_per_request"]
        database_writes = monthly_requests * base["db_writes_per_request"]

        monthly_files = profile.monthly_file_uploads()
        file_gb = profile.average_file_size_gb()
        if monthly_files > 0:
            upload_storage_gb = monthly_files * file_gb
            outbound_network_gb += upload_storage_gb * 0.4
            monthly_requests += monthly_files * 1.5
            database_writes += monthly_files * 0.5
            if profile.background_jobs != "none":
                cpu_seconds += monthly_files * duration_sec * cpu_vcpu * 2.0

        bg_multiplier = profile.background_multiplier()
        queue_messages = users * base["queue_messages_per_user"] * max(bg_multiplier, 0.25)
        if profile.background_jobs != "none" and monthly_files > 0:
            queue_messages += monthly_files

        ai_requests_per_day = profile.ai_requests_per_user_per_day_value()
        ai_requests = users * ai_requests_per_day * active_days
        input_tokens = ai_requests * profile.prompt_tokens()
        output_tokens = ai_requests * profile.response_tokens()
        if ai_requests > 0:
            monthly_requests += ai_requests

        notification_volume = profile.monthly_notification_volume()
        channel_count = len(profile.notification_channels)
        emails_sent = 0.0
        push_notifications = 0.0
        sms_messages = 0.0
        if channel_count > 0:
            per_channel = notification_volume / channel_count
            if "email" in profile.notification_channels:
                emails_sent = per_channel
            if "push" in profile.notification_channels:
                push_notifications = per_channel
            if "sms" in profile.notification_channels:
                sms_messages = per_channel

        log_gb = min(
            (monthly_requests / 1000.0) * base["log_gb_per_1000_requests"],
            base.get("monitoring_log_gb_cap", 0.5),
        )
        metric_samples = min(
            monthly_requests * base["metric_samples_per_request"],
            base.get("monitoring_metric_samples_cap", 5000.0),
        )

        consumption = ResourceConsumption(
            monthly_active_users=float(users),
            monthly_requests=monthly_requests,
            cpu_seconds=cpu_seconds,
            memory_gib_seconds=memory_gib_seconds,
            storage_gb=storage_gb,
            outbound_network_gb=outbound_network_gb,
            database_reads=database_reads,
            database_writes=database_writes,
            database_storage_gb=database_storage_gb,
            queue_messages=queue_messages,
            cache_memory_gb=base["cache_memory_gb"],
            ai_requests=ai_requests,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            emails_sent=emails_sent,
            push_notifications=push_notifications,
            sms_messages=sms_messages,
            log_gb=log_gb,
            metric_samples=metric_samples,
            instance_hours=0.0,
            instances=0.0,
        )

        if stage == STAGE_PRODUCTION:
            consumption = self._apply_production_scale(consumption)
        return consumption

    @staticmethod
    def _apply_production_scale(consumption: ResourceConsumption) -> ResourceConsumption:
        scale = USAGE_STAGE_PRODUCTION_MULTIPLIER
        return ResourceConsumption(
            monthly_active_users=consumption.monthly_active_users,
            monthly_requests=consumption.monthly_requests * scale,
            cpu_seconds=consumption.cpu_seconds * scale,
            memory_gib_seconds=consumption.memory_gib_seconds * scale,
            storage_gb=consumption.storage_gb * scale,
            outbound_network_gb=consumption.outbound_network_gb * scale,
            database_reads=consumption.database_reads * scale,
            database_writes=consumption.database_writes * scale,
            database_storage_gb=consumption.database_storage_gb * scale,
            queue_messages=consumption.queue_messages * scale,
            cache_memory_gb=consumption.cache_memory_gb,
            ai_requests=consumption.ai_requests * scale,
            input_tokens=consumption.input_tokens * scale,
            output_tokens=consumption.output_tokens * scale,
            emails_sent=consumption.emails_sent * scale,
            push_notifications=consumption.push_notifications * scale,
            sms_messages=consumption.sms_messages * scale,
            log_gb=consumption.log_gb * scale,
            metric_samples=consumption.metric_samples * scale,
            instance_hours=consumption.instance_hours,
            instances=consumption.instances,
        )
