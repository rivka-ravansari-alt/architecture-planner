"""GCP meter unit scaling tests."""

from __future__ import annotations

from app.pricing.gcp.meter_scaling import GcpMeterUnitScaler


class TestGcpMeterUnitScaler:
    def setup_method(self) -> None:
        self.scaler = GcpMeterUnitScaler()

    def test_cloud_run_requests_to_requests(self) -> None:
        result = self.scaler.scale(100_000, "requests/month", "Requests")
        assert result == (100_000, "100,000 requests (direct)")

    def test_api_gateway_requests_to_per_million_meter(self) -> None:
        result = self.scaler.scale(1400, "requests/month", "1M requests")
        assert result == (0.0014, "1,400 ops / 1,000,000")

    def test_cloud_run_vcpu_hours_to_hrs(self) -> None:
        result = self.scaler.scale(730, "vCPU-hours/month", "Hrs")
        assert result == (730, "730 hours (direct)")

    def test_cloud_run_memory_gb_hours(self) -> None:
        result = self.scaler.scale(365, "GiB-hours/month", "Hrs")
        assert result == (365, "365 hours (direct)")

    def test_cloud_storage_gb_months(self) -> None:
        result = self.scaler.scale(50, "GB-months", "GB-Mo")
        assert result == (50, "50.0000 GB-months (direct)")

    def test_cloud_storage_operations_to_requests(self) -> None:
        result = self.scaler.scale(50_000, "operations/month", "Requests")
        assert result == (50_000, "50,000 operations (direct)")

    def test_bigquery_tb_scanned(self) -> None:
        result = self.scaler.scale(2.5, "TB/month", "TB")
        assert result == (2.5, "2.5000 TB (direct)")

    def test_gemini_tokens_per_1k(self) -> None:
        result = self.scaler.scale(500_000, "tokens/month", "1K Tokens")
        assert result == (500, "500,000 tokens / 1,000")
