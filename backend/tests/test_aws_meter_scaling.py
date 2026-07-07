"""AWS meter unit scaling tests."""

from __future__ import annotations

from app.pricing.aws.meter_scaling import AwsMeterUnitScaler


class TestAwsMeterUnitScaler:
    def setup_method(self) -> None:
        self.scaler = AwsMeterUnitScaler()

    def test_lambda_executions_to_requests(self) -> None:
        result = self.scaler.scale(100_000, "executions/month", "Requests")
        assert result == (100_000, "100,000 executions (direct)")

    def test_lambda_gb_seconds(self) -> None:
        result = self.scaler.scale(15_000, "GB-seconds/month", "GB-Seconds")
        assert result == (15_000, "15,000 GB-seconds (direct)")

    def test_rds_instance_hours_to_hrs(self) -> None:
        result = self.scaler.scale(730, "instance-hours/month", "Hrs")
        assert result == (730, "730 hours (direct)")

    def test_alb_hours_and_lcu(self) -> None:
        assert self.scaler.scale(730, "hours/month", "Hrs") == (730, "730 hours (direct)")
        assert self.scaler.scale(30, "LCU-hours/month", "LCU-Hrs") == (30, "30 LCU-hours (direct)")

    def test_ecs_fargate_compute_hours(self) -> None:
        assert self.scaler.scale(365, "vCPU-hours/month", "hours") == (365, "365 hours (direct)")
        assert self.scaler.scale(730, "GiB-hours/month", "hours") == (730, "730 hours (direct)")

    def test_s3_operations_to_requests(self) -> None:
        result = self.scaler.scale(50_000, "operations/month", "Requests")
        assert result == (50_000, "50,000 operations (direct)")
