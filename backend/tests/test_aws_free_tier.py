"""Tests for AWS free-tier pooling."""

from __future__ import annotations

from app.pricing.aws.free_tier import FreeTierPoolState, apply_project_free_tier
from app.pricing.aws.registry import get_aws_pricing_model
from app.pricing.aws.sku_quantities import calculate_aws_sku_quantities
from app.pricing.schemas import AssumptionConfidence, AssumptionSource, UsageAssumption


def _assumption(key: str, value: int | float | str) -> UsageAssumption:
    return UsageAssumption(
        key=key,
        value=value,
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning="test",
    )


class TestAwsFreeTier:
    def test_lambda_free_tier_deducts_requests(self) -> None:
        model = get_aws_pricing_model("Lambda")
        assert model is not None
        resolved = [
            _assumption("executions_per_month", 2_000_000),
            _assumption("avg_execution_duration_ms", 100),
            _assumption("memory_mb", 128),
            _assumption("network_egress_gb", 0),
        ]
        raw = calculate_aws_sku_quantities(model, resolved)
        pool = FreeTierPoolState()
        adjusted = apply_project_free_tier(model, raw, pool, resolved=resolved)
        requests = next(q for q in adjusted.quantities if q.sku_key == "requests")
        assert requests.free_tier_deducted == 1_000_000
        assert requests.quantity == 1_000_000
