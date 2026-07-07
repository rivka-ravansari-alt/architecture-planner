"""Tests for GCP SKU quantity calculators."""

from __future__ import annotations

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


class TestGcpCloudRunSkuQuantities:
    def test_cloud_run_vcpu_and_memory_hours(self) -> None:
        model = get_gcp_pricing_model("Cloud Run")
        assert model is not None
        resolved = [
            _assumption("requests_per_month", 1_000_000),
            _assumption("avg_request_duration_seconds", 0.5),
            _assumption("cpu", 1.0),
            _assumption("memory_gb", 2.0),
            _assumption("network_egress_gb", 1.0),
            _assumption("min_instances", 0),
        ]
        result = calculate_gcp_sku_quantities(model, resolved)
        assert result.ready
        vcpu_hours = next(q for q in result.quantities if q.sku_key == "vcpu_hours")
        memory_gb_hours = next(q for q in result.quantities if q.sku_key == "memory_gb_hours")
        expected_vcpu = 1_000_000 * 0.5 * 1.0 / 3600
        expected_memory = 1_000_000 * 0.5 * 2.0 / 3600
        assert vcpu_hours.quantity == expected_vcpu
        assert memory_gb_hours.quantity == expected_memory

    def test_cloud_run_min_instances_baseline(self) -> None:
        model = get_gcp_pricing_model("Cloud Run")
        assert model is not None
        resolved = [
            _assumption("requests_per_month", 10_000),
            _assumption("avg_request_duration_seconds", 0.1),
            _assumption("cpu", 1.0),
            _assumption("memory_gb", 1.0),
            _assumption("network_egress_gb", 0),
            _assumption("min_instances", 1),
        ]
        result = calculate_gcp_sku_quantities(model, resolved)
        assert result.ready
        vcpu_hours = next(q for q in result.quantities if q.sku_key == "vcpu_hours")
        assert vcpu_hours.quantity == 730.0


class TestGcpCloudStorageSkuQuantities:
    def test_cloud_storage_combined_requests(self) -> None:
        model = get_gcp_pricing_model("Cloud Storage")
        assert model is not None
        resolved = [
            _assumption("storage_gb", 100),
            _assumption("storage_class", "Standard"),
            _assumption("write_operations", 5000),
            _assumption("read_operations", 15000),
            _assumption("data_egress_gb", 2.0),
        ]
        result = calculate_gcp_sku_quantities(model, resolved)
        assert result.ready
        storage = next(q for q in result.quantities if q.sku_key == "storage_gb_month")
        requests = next(q for q in result.quantities if q.sku_key == "requests")
        assert storage.quantity == 100
        assert requests.quantity == 20_000


class TestGcpCloudSqlSkuQuantities:
    def test_cloud_sql_instance_and_storage(self) -> None:
        model = get_gcp_pricing_model("Cloud SQL")
        assert model is not None
        resolved = [
            _assumption("instance_tier", "db-f1-micro"),
            _assumption("storage_gb", 20),
            _assumption("backup_storage_gb", 5),
            _assumption("hours_per_month", 730),
        ]
        result = calculate_gcp_sku_quantities(model, resolved)
        assert result.ready
        instance_hours = next(q for q in result.quantities if q.sku_key == "instance_hours")
        storage = next(q for q in result.quantities if q.sku_key == "storage_gb_month")
        backup = next(q for q in result.quantities if q.sku_key == "backup_storage_gb_month")
        assert instance_hours.quantity == 730
        assert storage.quantity == 10
        assert storage.raw_quantity == 20
        assert backup.quantity == 5
