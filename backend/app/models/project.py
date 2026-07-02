from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base
from app.models._helpers import _now, _uuid

if TYPE_CHECKING:
    from app.models.user import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    project_types: Mapped[list] = mapped_column(JSON, default=list)
    stage: Mapped[str] = mapped_column(String(20), default="mvp")
    expected_users: Mapped[str] = mapped_column(String(20), default="100")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    workflow_status: Mapped[str] = mapped_column(String(40), default="DRAFT")

    main_flow: Mapped[list] = mapped_column(JSON, default=list)
    next_steps: Mapped[list] = mapped_column(JSON, default=list)
    architecture_summary: Mapped[str] = mapped_column(Text, default="")
    architecture_diagram: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    architecture_diagrams: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    answers: Mapped[RequirementAnswers | None] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    components: Mapped[list[ProjectComponent]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectComponent.order",
    )
    cost_estimates: Mapped[list[CostEstimate]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    risks: Mapped[list[Risk]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list[Recommendation]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    owner: Mapped["User | None"] = relationship(back_populates="projects")


class RequirementAnswers(Base):
    __tablename__ = "requirement_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    auth: Mapped[bool] = mapped_column(Boolean, default=False)
    file_upload: Mapped[bool] = mapped_column(Boolean, default=False)
    background_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    dashboards: Mapped[bool] = mapped_column(Boolean, default=False)
    ai: Mapped[bool] = mapped_column(Boolean, default=False)
    payments: Mapped[bool] = mapped_column(Boolean, default=False)
    include_edge_cases: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship(back_populates="answers")


class ProjectComponent(Base):
    __tablename__ = "project_components"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    key: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(120))
    component_type: Mapped[str] = mapped_column(String(40), default="api")
    reason: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(20), default="core")
    source: Mapped[str] = mapped_column(String(20), default="ai_generated")
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped[Project] = relationship(back_populates="components")
    cloud_mapping: Mapped[CloudMapping | None] = relationship(
        back_populates="component", cascade="all, delete-orphan", uselist=False
    )


class CloudMapping(Base):
    __tablename__ = "cloud_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    component_id: Mapped[str] = mapped_column(
        ForeignKey("project_components.id", ondelete="CASCADE")
    )

    aws: Mapped[str | None] = mapped_column(JSON, nullable=True)
    gcp: Mapped[str | None] = mapped_column(JSON, nullable=True)
    azure: Mapped[str | None] = mapped_column(JSON, nullable=True)

    component: Mapped[ProjectComponent] = relationship(back_populates="cloud_mapping")


class CostEstimate(Base):
    __tablename__ = "cost_estimates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    provider: Mapped[str] = mapped_column(String(20))
    monthly_low: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_high: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    notes: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[Project] = relationship(back_populates="cost_estimates")


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(20), default="medium")

    project: Mapped[Project] = relationship(back_populates="risks")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[Project] = relationship(back_populates="recommendations")

