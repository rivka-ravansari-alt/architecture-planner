"""Map architecture-wide consumption to per-component resource slices."""

from __future__ import annotations

from dataclasses import replace

from app.schemas.domain import MappedComponent
from app.services.usage_estimation.models import ResourceConsumption
from app.services.usage_estimation.usage_baseline import resolve_hosting_instance_metrics

_REQUEST_ONLY_KEYS = frozenset({"cdn", "load_balancer", "api_gateway"})
_COMPUTE_KEYS = frozenset({"service", "worker"})
_HOSTING_KEYS = frozenset({"web_app", "mobile_app", "admin_panel"})
_DATABASE_KEYS = frozenset({"database", "search"})
_STORAGE_KEYS = frozenset({"object_storage"})
_CACHE_KEYS = frozenset({"cache"})
_QUEUE_KEYS = frozenset({"queue"})
_AI_KEYS = frozenset({"ai_provider"})
_NOTIFICATION_KEYS = frozenset({"notification"})
_MONITORING_KEYS = frozenset({"monitoring", "logging", "tracing", "alerting", "analytics"})
_SKIP_KEYS = frozenset({"user", "external_api", "payment", "secrets", "config"})


def _empty_consumption() -> ResourceConsumption:
    return ResourceConsumption()


class ComponentUsageAllocator:
    """Assigns relevant resource metrics to each architecture component."""

    def allocate_all(
        self,
        components: list[MappedComponent],
        global_consumption: ResourceConsumption,
        *,
        stage: str = "mvp",
    ) -> dict[str, ResourceConsumption]:
        billable = [c for c in components if not self._should_skip(c)]
        compute_count = sum(1 for c in billable if c.key in _COMPUTE_KEYS)
        hosting_count = sum(1 for c in billable if c.key in _HOSTING_KEYS)
        monitoring_count = sum(1 for c in billable if c.key in _MONITORING_KEYS)
        users = int(global_consumption.monthly_active_users) or 1
        hosting_hours, hosting_instances = resolve_hosting_instance_metrics(users, stage)

        allocations: dict[str, ResourceConsumption] = {}
        for component in billable:
            allocations[component.key] = self._allocate_one(
                component,
                global_consumption,
                compute_count=compute_count or 1,
                hosting_count=hosting_count or 1,
                monitoring_count=monitoring_count or 1,
                hosting_hours=hosting_hours,
                hosting_instances=hosting_instances,
            )
        return allocations

    def allocate(
        self,
        component: MappedComponent,
        global_consumption: ResourceConsumption,
        components: list[MappedComponent],
        *,
        stage: str = "mvp",
    ) -> ResourceConsumption:
        billable = [c for c in components if not self._should_skip(c)]
        users = int(global_consumption.monthly_active_users) or 1
        hosting_hours, hosting_instances = resolve_hosting_instance_metrics(users, stage)
        return self._allocate_one(
            component,
            global_consumption,
            compute_count=sum(1 for c in billable if c.key in _COMPUTE_KEYS) or 1,
            hosting_count=sum(1 for c in billable if c.key in _HOSTING_KEYS) or 1,
            monitoring_count=sum(1 for c in billable if c.key in _MONITORING_KEYS) or 1,
            hosting_hours=hosting_hours,
            hosting_instances=hosting_instances,
        )

    def _allocate_one(
        self,
        component: MappedComponent,
        global_consumption: ResourceConsumption,
        *,
        compute_count: int,
        hosting_count: int,
        monitoring_count: int,
        hosting_hours: float,
        hosting_instances: float,
    ) -> ResourceConsumption:
        key = component.key
        g = global_consumption

        if key in _REQUEST_ONLY_KEYS:
            return replace(_empty_consumption(), monthly_requests=g.monthly_requests)

        if key in _COMPUTE_KEYS:
            share = 1.0 / compute_count
            return replace(
                _empty_consumption(),
                monthly_requests=g.monthly_requests * share,
                cpu_seconds=g.cpu_seconds * share,
                memory_gib_seconds=g.memory_gib_seconds * share,
            )

        if key in _HOSTING_KEYS:
            share = 1.0 / hosting_count
            return replace(
                _empty_consumption(),
                monthly_requests=g.monthly_requests * share * 0.3,
                outbound_network_gb=g.outbound_network_gb * share,
                instance_hours=hosting_hours * share,
                instances=hosting_instances * share,
            )

        if key in _DATABASE_KEYS:
            return replace(
                _empty_consumption(),
                database_reads=g.database_reads,
                database_writes=g.database_writes,
                database_storage_gb=g.database_storage_gb,
            )

        if key in _STORAGE_KEYS:
            return replace(
                _empty_consumption(),
                storage_gb=g.storage_gb,
                outbound_network_gb=g.outbound_network_gb * 0.5,
            )

        if key in _CACHE_KEYS:
            return replace(_empty_consumption(), cache_memory_gb=g.cache_memory_gb)

        if key in _QUEUE_KEYS:
            return replace(_empty_consumption(), queue_messages=g.queue_messages)

        if key in _AI_KEYS:
            return replace(
                _empty_consumption(),
                ai_requests=g.ai_requests,
                input_tokens=g.input_tokens,
                output_tokens=g.output_tokens,
            )

        if key in _NOTIFICATION_KEYS:
            return replace(
                _empty_consumption(),
                emails_sent=g.emails_sent,
                push_notifications=g.push_notifications,
                sms_messages=g.sms_messages,
            )

        if key in _MONITORING_KEYS:
            share = 1.0 / monitoring_count
            return replace(
                _empty_consumption(),
                log_gb=g.log_gb * share,
                metric_samples=g.metric_samples * share,
            )

        return _empty_consumption()

    @staticmethod
    def _should_skip(component: MappedComponent) -> bool:
        if component.key in _SKIP_KEYS:
            return True
        recommended = str(component.implementation_options.get("recommended", "")).strip().lower()
        return recommended == "external_provider"
