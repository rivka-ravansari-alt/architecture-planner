from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=DESCRIPTION_MAX_CHARS)
    project_types: list[ProjectType] = Field(min_length=1)
    stage: Stage = Stage.mvp
    expected_users: ExpectedUsers = ExpectedUsers.u100
    answers: RequirementAnswersIn = RequirementAnswersIn()

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


class CostEstimateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    monthly_low: float
    monthly_high: float
    currency: str
    notes: str


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
