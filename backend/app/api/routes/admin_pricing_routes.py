"""Admin pricing ingestion routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.controllers.admin_pricing_controller import AdminPricingController
from app.core.dependencies import get_admin_pricing_controller, get_pricing_sync_principal
from app.pricing_ingestion.schemas.sync import (
    CombinedPricingSyncResponse,
    PricingSyncRequest,
    ProviderPricingSyncResponse,
)

router = APIRouter(prefix="/admin/pricing", tags=["admin-pricing"])


@router.post(
    "/sync",
    response_model=ProviderPricingSyncResponse | CombinedPricingSyncResponse,
)
def sync_pricing(
    request: PricingSyncRequest,
    principal: str = Depends(get_pricing_sync_principal),
    controller: AdminPricingController = Depends(get_admin_pricing_controller),
):
    """Sync cloud pricing catalogs into Firestore for the requested provider."""
    return controller.sync_pricing(request, triggered_by=principal)
