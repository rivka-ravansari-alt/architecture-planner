"""GCP implementation of PricingModelRegistry."""

from __future__ import annotations

from app.pricing.gcp.registry import get_gcp_pricing_model
from app.pricing.schemas import GcpServicePricingModel
from app.pricing.usage.protocols import PricingModelRegistry
from app.pricing.usage.schemas import CloudProvider


class GcpPricingModelRegistry(PricingModelRegistry):
    """Resolve GCP pricing models from catalog/cloud mapping names."""

    def provider(self) -> CloudProvider:
        return "gcp"

    def resolve_model(self, mapped_service_name: str) -> GcpServicePricingModel | None:
        return get_gcp_pricing_model(mapped_service_name)
