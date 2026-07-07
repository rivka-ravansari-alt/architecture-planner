"""Abstract base classes for the usage assumptions layer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.pricing.schemas import CloudServicePricingModel, UsageInputDefinition
from app.pricing.usage.schemas import CloudProvider, UsageContext, UsageInferenceResult


class PricingModelRegistry(ABC):
    """Lookup pricing model schemas for a cloud provider."""

    @abstractmethod
    def provider(self) -> CloudProvider: ...

    @abstractmethod
    def resolve_model(self, mapped_service_name: str) -> CloudServicePricingModel | None: ...

    def required_inputs(self, mapped_service_name: str) -> list[UsageInputDefinition]:
        model = self.resolve_model(mapped_service_name)
        if model is None:
            return []
        return list(model.pricing_model.required_inputs)


class UsageInferenceProvider(ABC):
    """Strategy for inferring usage assumptions from a UsageContext."""

    @abstractmethod
    def infer(self, context: UsageContext) -> UsageInferenceResult: ...


class UsageAssumptionsPromptBuilder(ABC):
    """Build LLM prompts from a UsageContext."""

    @abstractmethod
    def build(self, context: UsageContext) -> str: ...


class UsageAssumptionsResponseValidator(ABC):
    """Validate raw LLM JSON against a UsageContext."""

    @abstractmethod
    def validate(self, raw: str, context: UsageContext) -> UsageInferenceResult: ...
