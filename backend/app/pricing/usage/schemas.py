"""Cloud-agnostic schemas for usage assumption inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.pricing.schemas import ComponentPricingInput, UsageInputDefinition

CloudProvider = Literal["azure", "aws", "gcp"]
InferenceSource = Literal["llm", "heuristic_fallback", "heuristic_only", "user_provided"]


@dataclass(frozen=True)
class CloudServiceBinding:
    """Maps an architecture component to a billable cloud service."""

    provider: CloudProvider
    mapped_service_name: str
    pricing_model_id: str


@dataclass(frozen=True)
class ComponentUsageContext:
    """One component prepared for usage inference."""

    component_id: str
    name: str
    component_type: str
    optional: bool
    order: int
    reason: str
    cloud: CloudServiceBinding
    required_inputs: tuple[UsageInputDefinition, ...]
    behavioral_inputs: tuple[UsageInputDefinition, ...] = ()
    config_input_keys: frozenset[str] = frozenset()


@dataclass(frozen=True)
class UsageContext:
    """Immutable snapshot of application context for inference."""

    product_name: str
    description: str
    stage: str
    expected_users: int
    expected_users_label: str
    requirements: dict[str, bool]
    architecture_summary: str
    feature_flags: dict[str, bool]
    provider: CloudProvider
    components: tuple[ComponentUsageContext, ...]


@dataclass(frozen=True)
class UsageInferenceAudit:
    """Explainability record for one inference run."""

    prompt: str | None = None
    raw_response: str | None = None
    validation_errors: tuple[str, ...] = ()
    duration_seconds: float | None = None


@dataclass(frozen=True)
class UsageInferenceResult:
    """Output of the usage assumptions layer."""

    components: tuple[ComponentPricingInput, ...]
    inference_source: InferenceSource
    audit: UsageInferenceAudit
