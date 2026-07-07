"""Tests for GCP free-tier pooling."""

from __future__ import annotations

from app.pricing.gcp.free_tier import FreeTierPoolState, apply_project_free_tier
from app.pricing.gcp.registry import get_gcp_pricing_model
from app.pricing.gcp.sku_quantities import calculate_gcp_sku_quantities
from app.pricing.schemas import AssumptionConfidence, AssumptionSource, UsageAssumption


def _assumption(key: str, value: int | float | str) -> UsageAssumption:
    return UsageAssumption(
        key=key,
        value=value,
        source=AssumptionSource.inferred,
        confidence=AssumptionConfidence.high,
        reasoning="test",
    )


class TestGcpFreeTier:
    def test_cloud_run_free_tier_deducts_requests(self) -> None:
        model = get_gcp_pricing_model("Cloud Run")
        assert model is not None
        resolved = [
            _assumption("requests_per_month", 2_500_000),
            _assumption("avg_request_duration_seconds", 0.25),
            _assumption("cpu", 1.0),
            _assumption("memory_gb", 1.0),
            _assumption("network_egress_gb", 0),
            _assumption("min_instances", 0),
        ]
        raw = calculate_gcp_sku_quantities(model, resolved)
        pool = FreeTierPoolState()
        adjusted = apply_project_free_tier(model, raw, pool, resolved=resolved)
        requests = next(q for q in adjusted.quantities if q.sku_key == "requests")
        assert requests.free_tier_deducted == 2_000_000
        assert requests.quantity == 500_000

    def test_cloud_storage_standard_storage_deduction(self) -> None:
        model = get_gcp_pricing_model("Cloud Storage")
        assert model is not None
        resolved = [
            _assumption("storage_gb", 20),
            _assumption("storage_class", "Standard"),
            _assumption("write_operations", 0),
            _assumption("read_operations", 0),
            _assumption("data_egress_gb", 0),
        ]
        raw = calculate_gcp_sku_quantities(model, resolved)
        pool = FreeTierPoolState()
        adjusted = apply_project_free_tier(model, raw, pool, resolved=resolved)
        storage = next(q for q in adjusted.quantities if q.sku_key == "storage_gb_month")
        assert storage.free_tier_deducted == 5
        assert storage.quantity == 15
