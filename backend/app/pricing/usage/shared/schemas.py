"""Schemas for cloud-agnostic shared usage inference."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.pricing.schemas import ComponentPricingInput, UsageAssumption, UsageInputDefinition
from app.pricing.usage.schemas import InferenceSource, UsageInferenceAudit


@dataclass(frozen=True)
class SharedComponentUsageContext:
    """One architecture component prepared for shared LLM inference."""

    component_id: str
    name: str
    component_type: str
    optional: bool
    order: int
    reason: str
    behavioral_inputs: tuple[UsageInputDefinition, ...]
    config_input_keys: frozenset[str]


@dataclass(frozen=True)
class SharedUsageContext:
    """Application context for one shared LLM usage inference call."""

    product_name: str
    description: str
    stage: str
    expected_users: int
    expected_users_label: str
    requirements: dict[str, bool]
    architecture_summary: str
    feature_flags: dict[str, bool]
    components: tuple[SharedComponentUsageContext, ...]


@dataclass
class SharedComponentInference:
    """Validated cloud-agnostic assumptions for one component."""

    component_id: str
    order: int
    component_type: str
    behavioral: dict[str, UsageAssumption]
    config: dict[str, UsageAssumption]
    storage_breakdown: list[UsageAssumption] = field(default_factory=list)


@dataclass
class SharedUsageInferenceResult:
    """Output of the shared LLM usage inference call."""

    components: tuple[SharedComponentInference, ...]
    inference_source: InferenceSource
    audit: UsageInferenceAudit = field(default_factory=UsageInferenceAudit)


@dataclass
class ProviderUsageInferenceResult:
    """Provider-specific pricing inputs derived from shared inference."""

    components: tuple[ComponentPricingInput, ...]
    inference_source: InferenceSource
    warnings: tuple[str, ...] = ()
