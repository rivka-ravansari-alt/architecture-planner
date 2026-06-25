from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.config.params import COMPONENT_CATEGORY_MAIN
from app.core.database import Base
from app.models._helpers import _now, _uuid


class ComponentCatalog(Base):
    __tablename__ = "architecture_components"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(
        String(40), default=COMPONENT_CATEGORY_MAIN, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, default="")
    aws_options: Mapped[list] = mapped_column(JSON, default=list)
    gcp_options: Mapped[list] = mapped_column(JSON, default=list)
    azure_options: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
