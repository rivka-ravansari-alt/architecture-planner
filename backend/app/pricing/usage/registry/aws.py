"""AWS implementation of PricingModelRegistry."""

from __future__ import annotations

from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.schemas import AwsServicePricingModel
from app.pricing.usage.protocols import PricingModelRegistry
from app.pricing.usage.schemas import CloudProvider


class AwsPricingModelRegistry(PricingModelRegistry):
    """Resolve AWS pricing models from catalog/cloud mapping names."""

    def provider(self) -> CloudProvider:
        return "aws"

    def resolve_model(self, mapped_service_name: str) -> AwsServicePricingModel | None:
        return get_aws_pricing_model(mapped_service_name)
