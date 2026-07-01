"""Provider-independent resource consumption models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ProductCapabilities:
    auth: bool = False
    file_upload: bool = False
    background_processing: bool = False
    dashboards: bool = False
    ai: bool = False
    payments: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, bool] | None) -> ProductCapabilities:
        if not data:
            return cls()
        return cls(
            auth=bool(data.get("auth", False)),
            file_upload=bool(data.get("file_upload", False)),
            background_processing=bool(data.get("background_processing", False)),
            dashboards=bool(data.get("dashboards", False)),
            ai=bool(data.get("ai", False)),
            payments=bool(data.get("payments", False)),
        )


@dataclass(frozen=True)
class ResourceConsumption:
    """Normalized monthly resource consumption for an architecture or component."""

    monthly_active_users: float = 0.0
    monthly_requests: float = 0.0
    cpu_seconds: float = 0.0
    memory_gib_seconds: float = 0.0
    storage_gb: float = 0.0
    outbound_network_gb: float = 0.0
    database_reads: float = 0.0
    database_writes: float = 0.0
    database_storage_gb: float = 0.0
    queue_messages: float = 0.0
    cache_memory_gb: float = 0.0
    ai_requests: float = 0.0
    input_tokens: float = 0.0
    output_tokens: float = 0.0
    emails_sent: float = 0.0
    push_notifications: float = 0.0
    sms_messages: float = 0.0
    log_gb: float = 0.0
    metric_samples: float = 0.0
    instance_hours: float = 0.0
    instances: float = 0.0

    def to_pricing_metrics(self) -> dict[str, float]:
        """Flatten to a dict consumed by pricing calculators."""
        metrics = asdict(self)
        metrics["egress_gb"] = self.outbound_network_gb
        return metrics

    def with_scale(self, factor: float) -> ResourceConsumption:
        if factor == 1.0:
            return self
        return ResourceConsumption(
            **{key: value * factor for key, value in asdict(self).items()},
        )


@dataclass(frozen=True)
class ArchitectureUsageEstimate:
    """Global consumption for the whole architecture plus per-component slices."""

    expected_users: str
    stage: str
    capabilities: ProductCapabilities
    global_consumption: ResourceConsumption
    component_consumption: dict[str, ResourceConsumption] = field(default_factory=dict)
