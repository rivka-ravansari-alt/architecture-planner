"""Deterministic monthly cost estimation from Firestore pricing catalogs."""

from __future__ import annotations

import logging
from typing import Any

from app.config.params import CALCULATOR_VERSION_PROFILE_DRIVEN
from app.pricing_ingestion.repositories.firestore_provider import FirestoreClientFactory
from app.schemas.domain import MappedComponent, ProviderCost
from app.services.cost_calculation.architecture_cost_calculator import ArchitectureCostCalculator
from app.services.cost_calculation.pricing_catalog_repository import PricingCatalogRepository
from app.services.cost_calculation.pricing_profile_repository import PricingProfileRepository
from app.services.usage_estimation import ProductCapabilities

logger = logging.getLogger(__name__)


class CostEstimatorService:
    def __init__(
        self,
        *,
        cost_calculator: ArchitectureCostCalculator | None = None,
        firestore_client: Any | None = None,
    ) -> None:
        if cost_calculator is not None:
            self._calculator = cost_calculator
        else:
            client = firestore_client or FirestoreClientFactory.create()
            self._calculator = ArchitectureCostCalculator(
                PricingCatalogRepository(client),
                pricing_profiles=PricingProfileRepository(client),
            )

    def estimate_from_components(
        self,
        *,
        components: list[MappedComponent],
        expected_users: str,
        stage: str,
        capabilities: ProductCapabilities | dict[str, bool] | None = None,
        usage_profile: dict[str, object] | None = None,
    ) -> list[ProviderCost]:
        logger.info(
            "PROFILE_DRIVEN_COST_CALCULATOR_USED calculator_version=%s components=%s",
            CALCULATOR_VERSION_PROFILE_DRIVEN,
            len(components),
        )
        return self._calculator.calculate(
            components=components,
            expected_users=expected_users,
            stage=stage,
            capabilities=capabilities,
            usage_profile=usage_profile,
        )
