"""Build UsageContext from project and architecture components."""

from __future__ import annotations

from app.config.params import REQUIREMENT_KEYS
from app.models import Project
from app.pricing.usage.behavioral_models import get_behavioral_model
from app.pricing.usage.protocols import PricingModelRegistry
from app.pricing.usage.registry.aws import AwsPricingModelRegistry
from app.pricing.usage.registry.azure import AzurePricingModelRegistry
from app.pricing.usage.registry.gcp import GcpPricingModelRegistry
from app.pricing.usage.schemas import (
    CloudProvider,
    CloudServiceBinding,
    ComponentUsageContext,
    UsageContext,
)
from app.schemas.domain import MappedComponent

_USER_BAND_MAU: dict[str, int] = {
    "100": 100,
    "1000": 1_000,
    "10000": 10_000,
    "100000+": 100_000,
}

_PROVIDERS: dict[CloudProvider, PricingModelRegistry] = {
    "azure": AzurePricingModelRegistry(),
    "aws": AwsPricingModelRegistry(),
    "gcp": GcpPricingModelRegistry(),
}


class UsageContextBuilder:
    """Normalize project inputs into a cloud-agnostic UsageContext."""

    def __init__(
        self,
        *,
        registries: dict[CloudProvider, PricingModelRegistry] | None = None,
    ) -> None:
        self._registries = registries or dict(_PROVIDERS)

    def build(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        provider: CloudProvider = "azure",
        feature_flags: dict[str, bool] | None = None,
    ) -> UsageContext:
        registry = self._registries.get(provider)
        if registry is None:
            raise ValueError(f"No pricing model registry for provider {provider!r}.")

        priced_components = self._priced_components(components, registry)
        if not priced_components:
            raise ValueError(
                f"No {provider}-mapped components found for usage assumption inference."
            )

        requirements = self._requirements(project)
        return UsageContext(
            product_name=project.name,
            description=project.description or "",
            stage=project.stage or "mvp",
            expected_users=_USER_BAND_MAU.get(project.expected_users or "100", 100),
            expected_users_label=project.expected_users or "100",
            requirements=requirements,
            architecture_summary=project.architecture_summary or "",
            feature_flags=dict(feature_flags or {}),
            provider=provider,
            components=tuple(priced_components),
        )

    @staticmethod
    def _requirements(project: Project) -> dict[str, bool]:
        answers = project.answers
        return {
            key: getattr(answers, key, False) if answers else False
            for key in REQUIREMENT_KEYS
        }

    def _priced_components(
        self,
        components: list[MappedComponent],
        registry: PricingModelRegistry,
    ) -> list[ComponentUsageContext]:
        priced: list[ComponentUsageContext] = []
        for component in sorted(components, key=lambda item: item.order):
            mapped_name = component.cloud.get(registry.provider())
            if not mapped_name:
                continue
            model = registry.resolve_model(str(mapped_name))
            if model is None:
                continue
            behavioral_model = get_behavioral_model(model.service, provider=registry.provider())
            behavioral_inputs = (
                behavioral_model.behavioral_inputs if behavioral_model else ()
            )
            config_keys = (
                behavioral_model.config_input_keys if behavioral_model else frozenset()
            )
            priced.append(
                ComponentUsageContext(
                    component_id=component.key,
                    name=component.name,
                    component_type=component.component_type,
                    optional=component.optional,
                    order=component.order,
                    reason=component.reason or "",
                    cloud=CloudServiceBinding(
                        provider=registry.provider(),
                        mapped_service_name=str(mapped_name),
                        pricing_model_id=model.service,
                    ),
                    required_inputs=tuple(model.pricing_model.required_inputs),
                    behavioral_inputs=behavioral_inputs,
                    config_input_keys=config_keys,
                )
            )
        return priced
