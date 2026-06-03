from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    google_sub: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), default="")
    name: Mapped[str] = mapped_column(String(200), default="")
    picture: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    projects: Mapped[list[Project]] = relationship(back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    # Multi-select project types, e.g. ["web_app", "mobile_app"].
    project_types: Mapped[list] = mapped_column(JSON, default=list)
    stage: Mapped[str] = mapped_column(String(20), default="mvp")
    expected_users: Mapped[str] = mapped_column(String(20), default="100")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    main_flow: Mapped[list] = mapped_column(JSON, default=list)
    next_steps: Mapped[list] = mapped_column(JSON, default=list)
    architecture_summary: Mapped[str] = mapped_column(Text, default="")
    architecture_diagram: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # legacy
    architecture_diagrams: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    answers: Mapped[RequirementAnswers | None] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    components: Mapped[list[ArchitectureComponent]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ArchitectureComponent.order"
    )
    cost_estimates: Mapped[list[CostEstimate]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    risks: Mapped[list[Risk]] = relationship(back_populates="project", cascade="all, delete-orphan")
    recommendations: Mapped[list[Recommendation]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    owner: Mapped[User | None] = relationship(back_populates="projects")


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


class ArchitectureComponent(Base):
    __tablename__ = "architecture_components"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    key: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(120))
    component_type: Mapped[str] = mapped_column(String(40), default="api")
    reason: Mapped[str] = mapped_column(Text, default="")
    # core | conditional | production | optional
    category: Mapped[str] = mapped_column(String(20), default="core")
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
        ForeignKey("architecture_components.id", ondelete="CASCADE")
    )

    aws: Mapped[list] = mapped_column(JSON, default=list)
    gcp: Mapped[list] = mapped_column(JSON, default=list)
    azure: Mapped[list] = mapped_column(JSON, default=list)

    component: Mapped[ArchitectureComponent] = relationship(back_populates="cloud_mapping")


class CostEstimate(Base):
    __tablename__ = "cost_estimates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    provider: Mapped[str] = mapped_column(String(20))  # aws | gcp | azure
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
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low | medium | high

    project: Mapped[Project] = relationship(back_populates="risks")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[Project] = relationship(back_populates="recommendations")


class ArchitectureGenerationRequest(Base):
    """Tracks the lifecycle of a single architecture generation run."""

    __tablename__ = "architecture_generation_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_os_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_os_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
