"""Build cloud-agnostic usage context for shared LLM inference."""

from __future__ import annotations

from app.config.params import REQUIREMENT_KEYS
from app.models import Project
from app.pricing.usage.component_type_behavioral_models import get_component_type_behavioral_model
from app.pricing.usage.shared.schemas import SharedComponentUsageContext, SharedUsageContext
from app.schemas.domain import MappedComponent

_USER_BAND_MAU: dict[str, int] = {
    "100": 100,
    "1000": 1_000,
    "10000": 10_000,
    "100000+": 100_000,
}


class SharedUsageContextBuilder:
    """Normalize project inputs into a provider-neutral UsageContext."""

    def build(
        self,
        project: Project,
        components: list[MappedComponent],
        *,
        feature_flags: dict[str, bool] | None = None,
    ) -> SharedUsageContext:
        priced_components = self._priced_components(components)
        if not priced_components:
            raise ValueError("No architecture components found for shared usage inference.")

        return SharedUsageContext(
            product_name=project.name,
            description=project.description or "",
            stage=project.stage or "mvp",
            expected_users=_USER_BAND_MAU.get(project.expected_users or "100", 100),
            expected_users_label=project.expected_users or "100",
            requirements=self._requirements(project),
            architecture_summary=project.architecture_summary or "",
            feature_flags=dict(feature_flags or {}),
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
    ) -> list[SharedComponentUsageContext]:
        priced: list[SharedComponentUsageContext] = []
        for component in sorted(components, key=lambda item: item.order):
            model = get_component_type_behavioral_model(component.component_type)
            if model is None:
                continue
            priced.append(
                SharedComponentUsageContext(
                    component_id=component.key,
                    name=component.name,
                    component_type=component.component_type,
                    optional=component.optional,
                    order=component.order,
                    reason=component.reason or "",
                    behavioral_inputs=model.behavioral_inputs,
                    config_input_keys=model.config_input_keys,
                )
            )
        return priced
