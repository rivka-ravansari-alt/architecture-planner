"""Tests for usage input validation before pricing."""

from __future__ import annotations

import pytest

from app.services.pricing_calculation_executor import PricingCalculationError
from app.validators.usage_inputs_validator import validate_cosmos_db_inputs


def test_validate_cosmos_db_inputs_accepts_serverless_with_request_units():
    validate_cosmos_db_inputs(
        {
            "capacity_mode": "Serverless",
            "request_units_per_month": 500_000,
            "database_storage_gb": 10,
        }
    )


def test_validate_cosmos_db_inputs_accepts_provisioned_with_required_ru():
    validate_cosmos_db_inputs(
        {
            "capacity_mode": "Provisioned Throughput",
            "required_ru_per_second": 400,
            "database_storage_gb": 10,
        }
    )


def test_validate_cosmos_db_inputs_rejects_numeric_capacity_mode():
    with pytest.raises(PricingCalculationError, match="string enum"):
        validate_cosmos_db_inputs({"capacity_mode": 1.0})


def test_validate_cosmos_db_inputs_rejects_invalid_capacity_mode():
    with pytest.raises(PricingCalculationError, match="must be one of"):
        validate_cosmos_db_inputs({"capacity_mode": "Dedicated"})


def test_validate_cosmos_db_inputs_requires_request_units_for_serverless():
    with pytest.raises(PricingCalculationError, match="request_units_per_month"):
        validate_cosmos_db_inputs(
            {
                "capacity_mode": "Serverless",
                "database_storage_gb": 10,
            }
        )


def test_validate_cosmos_db_inputs_requires_required_ru_for_provisioned():
    with pytest.raises(PricingCalculationError, match="required_ru_per_second"):
        validate_cosmos_db_inputs(
            {
                "capacity_mode": "Autoscale",
                "database_storage_gb": 10,
            }
        )
