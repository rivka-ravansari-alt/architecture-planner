from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.config.params import COMPONENT_SOURCE_AI, DESCRIPTION_MAX_CHARS
from app.schemas.enums import ExpectedUsers, ProjectType, Stage, WorkflowStatus


class RequirementAnswersIn(BaseModel):
    auth: bool = False
    file_upload: bool = False
    background_processing: bool = False
    dashboards: bool = False
    ai: bool = False
    payments: bool = False
    include_edge_cases: bool = False


class UsageProfileIn(BaseModel):
    monthly_active_users: str = "100"
    custom_monthly_active_users: int | None = None
    user_activity: str = "moderate"
    file_uploads_enabled: bool = False
    files_per_month: str = "under_1k"
    average_file_size: str = "small"
    ai_enabled: bool = False
    ai_requests_per_user_per_day: str = "under_1"
    prompt_size: str = "small"
    response_size: str = "medium"
    background_jobs: str = "none"
    notification_channels: list[str] = Field(default_factory=list)
    notifications_per_month: str = "under_1k"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=DESCRIPTION_MAX_CHARS)
    project_types: list[ProjectType] = Field(min_length=1)
    stage: Stage = Stage.mvp
    expected_users: str = ExpectedUsers.u100.value
    answers: RequirementAnswersIn = RequirementAnswersIn()
    usage_profile: UsageProfileIn | None = None

    @field_validator("expected_users", mode="before")
    @classmethod
    def validate_expected_users(cls, value: object) -> str:
        if isinstance(value, bool):
            raise ValueError("expected_users must be a known tier or positive integer.")
        if isinstance(value, (int, float)):
            count = int(value)
            if count < 1:
                raise ValueError("expected_users must be a positive integer.")
            return str(count)

        normalized = str(value).strip()
        if normalized in {item.value for item in ExpectedUsers}:
            return normalized
        try:
            count = int(normalized)
        except ValueError as exc:
            raise ValueError("expected_users must be a known tier or positive integer.") from exc
        if count < 1:
            raise ValueError("expected_users must be a positive integer.")
        return str(count)

    @field_validator("project_types")
    @classmethod
    def dedupe_types(cls, value: list[ProjectType]) -> list[ProjectType]:
        seen: list[ProjectType] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, value: str) -> str:
        if len(value) > DESCRIPTION_MAX_CHARS:
            raise ValueError(
                f"Project description must be {DESCRIPTION_MAX_CHARS} characters or fewer."
            )
        return value

    @field_validator("stage")
    @classmethod
    def reject_disabled_production_stage(cls, value: Stage) -> Stage:
        if value == Stage.production:
            raise ValueError("Production stage is not available yet. Use MVP for now.")
        return value


class CloudMappingIn(BaseModel):
    aws: list[str] = []
    gcp: list[str] = []
    azure: list[str] = []


class ComponentUpdateIn(BaseModel):
    key: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=120)
    type: str = Field(min_length=1, max_length=40)
    reason: str = ""
    optional: bool = False
    source: str = COMPONENT_SOURCE_AI
    cloud_mapping: CloudMappingIn | None = None
    implementation_options: dict[str, object] | None = None


class ComponentsUpdate(BaseModel):
    components: list[ComponentUpdateIn] = Field(min_length=1)


class CloudMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    aws: list[str]
    gcp: list[str]
    azure: list[str]


class ComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    key: str
    name: str
    type: str = Field(
        validation_alias="component_type", serialization_alias="type", default="api"
    )
    reason: str
    category: str
    source: str = COMPONENT_SOURCE_AI
    optional: bool
    order: int
    cloud_mapping: CloudMappingOut | None = None
    implementation_options: dict[str, object] | None = None


class SkuLineItemOut(BaseModel):
    sku_role: str
    sku_name: str | None = None
    sku_id: str | None = None
    usage_unit: str | None = None
    unit_price: float | None = None
    usage_metric: str | None = None
    conversion: str | None = None
    calculated_quantity: float
    quantity_note: str
    line_item_cost: float


class ComponentCostBreakdownOut(BaseModel):
    provider: str | None = None
    component_key: str
    component_type: str
    component_name: str
    status: str | None = None
    selected_cloud_service: str
    pricing_record_id: str
    pricing_record_name: str
    pricing_profile_id: str | None = None
    pricing_profile_service: str | None = None
    pricing_model: str
    billable_sku_roles: list[str] = []
    ignored_sku_roles: list[str] = []
    formula: dict[str, str] | str | None = None
    expected_users: str
    usage_assumptions: dict[str, float]
    sku_lines: list[SkuLineItemOut]
    warnings: list[str] = []
    component_monthly_cost: float | None = None
    final_component_cost: float
    included_in_total: bool = True
    exclusion_reason: str | None = None
    optional: bool


class CostEstimateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    monthly_low: float
    monthly_high: float
    required_monthly_low: float = 0.0
    required_monthly_high: float = 0.0
    optional_monthly_low: float = 0.0
    optional_monthly_high: float = 0.0
    currency: str
    notes: str
    calculator_version: str | None = None
    unknown_items: list[str] = []
    warnings: list[str] = []
    component_breakdown: list[ComponentCostBreakdownOut] = []
    pricing_debug_table: list[ComponentCostBreakdownOut] = []

    @model_validator(mode="after")
    def sync_monthly_with_required_only(self) -> CostEstimateOut:
        """Ensure monthly totals never include optional add-ons."""
        self.monthly_low = self.required_monthly_low
        self.monthly_high = self.required_monthly_high
        if not self.pricing_debug_table and self.component_breakdown:
            self.pricing_debug_table = list(self.component_breakdown)
        if not self.component_breakdown and self.pricing_debug_table:
            self.component_breakdown = list(self.pricing_debug_table)
        return self


class DiagramNodeOut(BaseModel):
    id: str
    name: str
    group: str | None = None
    type: str | None = None


class DiagramEdgeOut(BaseModel):
    source: str
    target: str
    label: str | None = None


class ArchitectureDiagramOut(BaseModel):
    type: str
    nodes: list[DiagramNodeOut] = []
    edges: list[DiagramEdgeOut] = []
    content: str | None = None


class DiagramViewOut(BaseModel):
    title: str
    nodes: list[DiagramNodeOut] = []
    edges: list[DiagramEdgeOut] = []


class ArchitectureDiagramsOut(BaseModel):
    high_level: DiagramViewOut
    system_flow: DiagramViewOut
    technical_architecture: DiagramViewOut


class AnswersOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    auth: bool
    file_upload: bool
    background_processing: bool
    dashboards: bool
    ai: bool
    payments: bool
    include_edge_cases: bool
    usage_profile: dict[str, object] | None = None


class ProjectDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    project_types: list[str]
    stage: str
    expected_users: str
    created_at: datetime
    generated_at: datetime | None = None
    workflow_status: WorkflowStatus = WorkflowStatus.draft
    main_flow: list[str] = []
    architecture_summary: str = ""
    architecture_diagram: ArchitectureDiagramOut | None = None
    architecture_diagrams: ArchitectureDiagramsOut | None = None
    answers: AnswersOut | None = None
    components: list[ComponentOut] = []
    cost_estimates: list[CostEstimateOut] = []


class ProjectTypeInfo(BaseModel):
    id: str
    label: str
    description: str


class ComponentCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    category: str
    description: str
    aws_options: list[str]
    gcp_options: list[str]
    azure_options: list[str]
    is_active: bool

    @field_validator("aws_options", mode="before")
    @classmethod
    def normalize_aws_options(cls, value: object) -> list[str]:
        from app.utils.cloud_catalog_options import cloud_options_as_strings

        return cloud_options_as_strings("aws", value)

    @field_validator("gcp_options", mode="before")
    @classmethod
    def normalize_gcp_options(cls, value: object) -> list[str]:
        from app.utils.cloud_catalog_options import cloud_options_as_strings

        return cloud_options_as_strings("gcp", value)

    @field_validator("azure_options", mode="before")
    @classmethod
    def normalize_azure_options(cls, value: object) -> list[str]:
        from app.utils.cloud_catalog_options import cloud_options_as_strings

        return cloud_options_as_strings("azure", value)
