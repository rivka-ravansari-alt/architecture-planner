from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.params import DESCRIPTION_MAX_TOKENS
from app.schemas.enums import ExpectedUsers, ProjectType, Stage
from app.utils.token_estimate import estimate_token_count


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
    description: str = Field(min_length=1, max_length=DESCRIPTION_MAX_TOKENS * 4)
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
        if estimate_token_count(value) > DESCRIPTION_MAX_TOKENS:
            raise ValueError(
                f"Project description must be {DESCRIPTION_MAX_TOKENS} tokens or fewer."
            )
        return value


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
    optional: bool
    order: int
    cloud_mapping: CloudMappingOut | None = None


class CostEstimateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    provider: str
    monthly_low: float
    monthly_high: float
    currency: str
    notes: str


class RiskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    description: str
    severity: str


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str


class DiagramNodeOut(BaseModel):
    id: str
    name: str
    group: str | None = None


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
    technical_flow: DiagramViewOut


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
    main_flow: list[str] = []
    next_steps: list[str] = []
    architecture_summary: str = ""
    architecture_diagram: ArchitectureDiagramOut | None = None
    architecture_diagrams: ArchitectureDiagramsOut | None = None
    answers: AnswersOut | None = None
    components: list[ComponentOut] = []
    cost_estimates: list[CostEstimateOut] = []
    risks: list[RiskOut] = []
    recommendations: list[RecommendationOut] = []


class ProjectTypeInfo(BaseModel):
    id: str
    label: str
    description: str
