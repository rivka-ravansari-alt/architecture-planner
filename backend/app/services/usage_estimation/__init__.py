"""Provider-independent usage estimation from users, architecture, and capabilities."""

from app.services.usage_estimation.component_usage_allocator import ComponentUsageAllocator
from app.services.usage_estimation.models import (
    ArchitectureUsageEstimate,
    ProductCapabilities,
    ResourceConsumption,
)
from app.services.usage_estimation.usage_estimator import UsageEstimator
from app.services.usage_estimation.usage_baseline import parse_active_user_count
from app.services.usage_estimation.usage_profile import UsageProfile

__all__ = [
    "ArchitectureUsageEstimate",
    "ComponentUsageAllocator",
    "ProductCapabilities",
    "ResourceConsumption",
    "UsageEstimator",
    "UsageProfile",
    "parse_active_user_count",
]
