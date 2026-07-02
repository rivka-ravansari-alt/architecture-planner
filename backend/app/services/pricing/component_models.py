"""Build component pricing plans from architecture type + Firestore catalog."""

from __future__ import annotations

from typing import Any

from app.schemas.domain import RequirementContext
from app.services.pricing.component_profiles import resolve_component_profile_with_source
from app.services.pricing.profile_engine import ComponentModelPlan, build_plan_from_profile
from app.services.pricing.usage_profile import UsageProfile


def build_component_model(
    *,
    component_type: str,
    provider: str,
    service_name: str,
    skus: dict[str, dict[str, Any]],
    profile: UsageProfile,
    stage: str,
    expected_users: str,
    requirements: RequirementContext,
    profile_repository: Any | None = None,
    allow_profile_fallback: bool = False,
) -> ComponentModelPlan:
    normalized = _normalize_type(component_type)
    resolution = resolve_component_profile_with_source(
        normalized,
        service_name,
        provider=provider,
        repository=profile_repository,
        allow_fallback=allow_profile_fallback,
    )
    if resolution.profile is None:
        return ComponentModelPlan(
            skus={},
            formula={"total": "0"},
            selection_notes=["Missing Firestore pricing profile."],
            profile=None,
            profile_resolution=resolution,
        )

    comp_profile = resolution.profile
    plan = build_plan_from_profile(
        comp_profile=comp_profile,
        skus=skus,
        usage=profile,
        stage=stage,
        expected_users=expected_users,
        requirements=requirements,
    )
    plan.profile_resolution = resolution
    plan.selection_notes.insert(
        0,
        f"Profile '{comp_profile.name}': formula={comp_profile.formula.value}, "
        f"required={[r.value for r in comp_profile.required_roles]}.",
    )
    return plan


def _normalize_type(component_type: str) -> str:
    from app.services.pricing.component_profiles import COMPONENT_TYPE_ALIASES

    return COMPONENT_TYPE_ALIASES.get(component_type, component_type)
