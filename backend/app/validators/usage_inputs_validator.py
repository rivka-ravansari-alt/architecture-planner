"""Validate flattened usage inputs before pricing scripts run."""

from __future__ import annotations

from typing import Any

from app.config.params import (
    COSMOS_DB_CAPACITY_MODES,
    COSMOS_DB_PROVISIONED_MODES,
    COSMOS_DB_SERVERLESS_MODE,
)
from app.services.pricing_calculation_executor import PricingCalculationError


def validate_cosmos_db_inputs(inputs: dict[str, Any]) -> None:
    """Validate Azure Cosmos DB pricing inputs."""

    mode = inputs.get("capacity_mode")
    if mode is None:
        raise PricingCalculationError(
            "capacity_mode is required for Azure Cosmos DB pricing."
        )
    if isinstance(mode, (int, float)):
        raise PricingCalculationError(
            "capacity_mode must be a string enum, not a number."
        )
    if not isinstance(mode, str) or mode not in COSMOS_DB_CAPACITY_MODES:
        allowed = ", ".join(sorted(COSMOS_DB_CAPACITY_MODES))
        raise PricingCalculationError(
            f"capacity_mode must be one of: {allowed}."
        )

    if mode == COSMOS_DB_SERVERLESS_MODE:
        request_units = inputs.get("request_units_per_month")
        if not isinstance(request_units, (int, float)) or float(request_units) <= 0:
            raise PricingCalculationError(
                "request_units_per_month must be populated for Serverless capacity mode."
            )
        return

    if mode in COSMOS_DB_PROVISIONED_MODES:
        required_ru = inputs.get("required_ru_per_second")
        if not isinstance(required_ru, (int, float)) or float(required_ru) < 0:
            raise PricingCalculationError(
                "required_ru_per_second must be populated for "
                "Provisioned Throughput or Autoscale capacity mode."
            )


def validate_service_inputs(service_id: str, inputs: dict[str, Any]) -> None:
    """Run service-specific usage input validation before pricing."""

    if service_id == "azure_cosmos_db":
        validate_cosmos_db_inputs(inputs)
