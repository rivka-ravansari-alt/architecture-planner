"""API schemas for pricing ingestion."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PricingProvider = Literal["gcp", "aws", "azure", "all"]


class PricingSyncRequest(BaseModel):
    provider: PricingProvider = "gcp"


class ImportRunErrorOut(BaseModel):
    service_id: str
    message: str


class ProviderPricingSyncResponse(BaseModel):
    provider: str
    import_run_id: str
    status: str
    started_at: datetime
    ended_at: datetime
    services_total: int
    services_succeeded: int
    services_failed: int
    skus_upserted: int
    errors: list[ImportRunErrorOut] = Field(default_factory=list)


class CombinedPricingSyncResponse(BaseModel):
    provider: Literal["all"] = "all"
    status: str
    started_at: datetime
    ended_at: datetime
    services_total: int
    services_succeeded: int
    services_failed: int
    skus_upserted: int
    providers: list[ProviderPricingSyncResponse] = Field(default_factory=list)


# Backward-compatible alias for existing GCP-focused code and tests.
GcpPricingSyncResponse = ProviderPricingSyncResponse
