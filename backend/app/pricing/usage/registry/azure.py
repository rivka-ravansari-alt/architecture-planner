"""Azure implementation of PricingModelRegistry."""

from __future__ import annotations

from app.pricing.azure.registry import get_azure_pricing_model
from app.pricing.schemas import AzureServicePricingModel
from app.pricing.usage.protocols import PricingModelRegistry
from app.pricing.usage.schemas import CloudProvider


class AzurePricingModelRegistry(PricingModelRegistry):
    """Resolve Azure pricing models from catalog/cloud mapping names."""

    def provider(self) -> CloudProvider:
        return "azure"

    def resolve_model(self, mapped_service_name: str) -> AzureServicePricingModel | None:
        return get_azure_pricing_model(mapped_service_name)
