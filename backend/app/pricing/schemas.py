"""Schemas for cloud pricing models and usage assumptions."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class AssumptionSource(str, Enum):
    user_provided = "user_provided"
    inferred = "inferred"
    default = "default"


class AssumptionConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class InputDataType(str, Enum):
    integer = "integer"
    float = "float"
    string = "string"
    boolean = "boolean"


class UsageInputDefinition(BaseModel):
    """Describes one usage input required by a pricing model."""

    key: str
    description: str
    unit: str
    data_type: InputDataType
    required: bool = True
    default_value: int | float | str | bool | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None


class CalculatedSkuDefinition(BaseModel):
    """Maps usage inputs to a billable SKU looked up in the pricing catalog."""

    key: str
    description: str
    unit: str
    input_keys: list[str] = Field(
        description="Usage inputs required to derive this SKU quantity."
    )
    catalog_sku_roles: list[str] = Field(
        description="SKU role keys in the Firestore pricing catalog document."
    )
    derivation: str = Field(
        description="Human-readable formula describing how inputs combine into this SKU."
    )


class ResourceRules(BaseModel):
    """Scaling and capacity constraints for the service."""

    supports_scale_to_zero: bool | None = None
    min_replicas_default: int | None = None
    max_replicas_default: int | None = None
    min_resources: dict[str, int | float | str] = Field(default_factory=dict)
    max_resources: dict[str, int | float | str] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)


class FreeTierAllowance(BaseModel):
    """Included monthly usage before metered billing applies."""

    allowances: dict[str, int | float] = Field(default_factory=dict)
    notes: str | None = None


class PricingModelDetails(BaseModel):
    """Usage assumptions and SKU mapping for one Azure service."""

    required_inputs: list[UsageInputDefinition]
    calculated_skus: list[CalculatedSkuDefinition]
    resource_rules: ResourceRules = Field(default_factory=ResourceRules)
    default_values: dict[str, int | float | str | bool] = Field(default_factory=dict)
    free_tier: FreeTierAllowance | None = None
    billing_unit: str
    billing_granularity: str
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AzureServicePricingModel(BaseModel):
    """Top-level pricing model definition for one Azure service."""

    cloud: Literal["azure"] = "azure"
    service: str
    component_types: list[str]
    catalog_service_name: str = Field(
        description="Display name used in component catalog cloud_mappings.azure."
    )
    pricing_model: PricingModelDetails


class AwsServicePricingModel(BaseModel):
    """Top-level pricing model definition for one AWS service."""

    cloud: Literal["aws"] = "aws"
    service: str
    component_types: list[str]
    catalog_service_name: str = Field(
        description="Display name used in component catalog cloud_mappings.aws."
    )
    pricing_model: PricingModelDetails


class GcpServicePricingModel(BaseModel):
    """Top-level pricing model definition for one GCP service."""

    cloud: Literal["gcp"] = "gcp"
    service: str
    component_types: list[str]
    catalog_service_name: str = Field(
        description="Display name used in component catalog cloud_mappings.gcp."
    )
    pricing_model: PricingModelDetails


CloudServicePricingModel = (
    AzureServicePricingModel | AwsServicePricingModel | GcpServicePricingModel
)


class UsageAssumption(BaseModel):
    """A resolved usage value with provenance."""

    key: str
    value: int | float | str | bool
    unit: str | None = None
    source: AssumptionSource
    confidence: AssumptionConfidence
    reasoning: str = ""


class MissingAssumption(BaseModel):
    """A required usage input that could not be resolved."""

    key: str
    description: str
    unit: str | None = None
    reason: str = "required for pricing calculation"


class AssumptionResolutionResult(BaseModel):
    """Output of resolving usage assumptions against a pricing model."""

    service: str
    resolved: list[UsageAssumption]
    missing: list[MissingAssumption]
    ready_for_calculation: bool


class SkuQuantity(BaseModel):
    """Deterministic SKU usage quantity derived from resolved assumptions."""

    sku_key: str
    quantity: float
    unit: str
    formula: str
    input_values_used: dict[str, int | float | str | bool]
    raw_quantity: float | None = None
    free_tier_deducted: float = 0
    free_tier_applied: bool = False
    notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IncludedUsage(BaseModel):
    """Usage included in a tier/package and excluded from billable SKU quantities."""

    sku_key: str
    quantity: float
    unit: str
    description: str
    source: Literal["tier", "free_tier", "plan"] = "tier"


class SkuQuantityResult(BaseModel):
    """SKU quantities for one Azure service; no dollar amounts."""

    service: str
    quantities: list[SkuQuantity]
    missing: list[MissingAssumption]
    included_usage: list[IncludedUsage] = Field(default_factory=list)
    ready: bool


class AdjustedSkuQuantityResult(BaseModel):
    """SKU quantities after tier inclusions and subscription free-tier pooling."""

    service: str
    quantities: list[SkuQuantity]
    included_usage: list[IncludedUsage]
    missing: list[MissingAssumption]
    ready: bool
    warnings: list[str] = Field(default_factory=list)


class ComponentPricingInput(BaseModel):
    """One architecture component ready for cloud SKU quantity calculation."""

    component_id: str
    order: int
    provider: Literal["azure", "aws", "gcp"] = "azure"
    cloud_service: str = ""
    azure_service: str = ""
    resolved: list[UsageAssumption]
    behavioral_assumptions: list[UsageAssumption] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_service_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cloud_service = data.get("cloud_service") or data.get("azure_service") or ""
        data["cloud_service"] = cloud_service
        data["azure_service"] = cloud_service
        data.setdefault("provider", "azure")
        return data


class ComponentSkuResult(BaseModel):
    """Adjusted SKU quantities for one project component."""

    component_id: str
    service: str
    quantities: list[SkuQuantity]
    included_usage: list[IncludedUsage]
    missing: list[MissingAssumption]
    ready: bool
    resolved: list[UsageAssumption] = Field(default_factory=list)
    behavioral_assumptions: list[UsageAssumption] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProjectSkuQuantityResult(BaseModel):
    """SKU quantities for a multi-component project with shared free-tier pools."""

    components: list[ComponentSkuResult]
    pool_summary: dict[str, Any] = Field(default_factory=dict)


class CatalogSkuPrice(BaseModel):
    """Unit price for one catalog SKU role from Firestore azure_catalog."""

    role: str
    unit_price_usd: float
    usage_unit: str
    description: str = ""
    sku_id: str | None = None
    meter_id: str | None = None


class MissingCatalogPrice(BaseModel):
    """A SKU line that could not be priced from the catalog."""

    catalog_service_name: str
    sku_key: str
    catalog_role: str | None = None
    reason: str


class SkuCostLine(BaseModel):
    """Monthly cost for one billable SKU quantity line."""

    sku_key: str
    catalog_role: str
    quantity: float
    unit: str
    billable_units: float
    unit_price_usd: float
    usage_unit: str
    monthly_cost_usd: float
    free_tier_applied: bool = False
    formula_note: str = ""
    warnings: list[str] = Field(default_factory=list)


class ComponentCostResult(BaseModel):
    """Priced SKU lines for one architecture component."""

    component_id: str
    service: str
    catalog_service_name: str
    line_items: list[SkuCostLine] = Field(default_factory=list)
    subtotal_usd: float = 0.0
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ready: bool = True
    pricing_status: Literal["supported", "partial", "unsupported", "ui_only"] = "supported"
    pricing_note: str | None = Field(
        default=None,
        description="Explanation when pricing_status is ui_only or otherwise non-catalog.",
    )
    unsupported_reason: str | None = None
    missing_implementation: list[str] = Field(default_factory=list)
    resolved_assumptions: list[UsageAssumption] = Field(default_factory=list)
    behavioral_assumptions: list[UsageAssumption] = Field(default_factory=list)
    optional: bool = False


class ProjectAzureCostResult(BaseModel):
    """Total Azure catalog-based cost for a project."""

    components: list[ComponentCostResult] = Field(default_factory=list)
    total_usd: float = 0.0
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    pool_summary: dict[str, Any] = Field(default_factory=dict)
    inference_source: str | None = Field(
        default=None,
        description="How usage assumptions were produced: llm, heuristic_fallback, heuristic_only.",
    )


class ProjectAwsCostResult(BaseModel):
    """Total AWS catalog-based cost for a project."""

    components: list[ComponentCostResult] = Field(default_factory=list)
    total_usd: float = 0.0
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    pool_summary: dict[str, Any] = Field(default_factory=dict)
    supported_component_count: int = 0
    unsupported_component_count: int = 0
    inference_source: str | None = Field(
        default=None,
        description="How usage assumptions were produced: llm, heuristic_fallback, heuristic_only.",
    )


class ProjectGcpCostResult(BaseModel):
    """Total GCP catalog-based cost for a project."""

    components: list[ComponentCostResult] = Field(default_factory=list)
    total_usd: float = 0.0
    missing_prices: list[MissingCatalogPrice] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    pool_summary: dict[str, Any] = Field(default_factory=dict)
    supported_component_count: int = 0
    unsupported_component_count: int = 0
    ui_only_component_count: int = 0
    inference_source: str | None = Field(
        default=None,
        description="How usage assumptions were produced: llm, heuristic_fallback, heuristic_only.",
    )
