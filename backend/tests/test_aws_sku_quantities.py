"""Tests for AWS SKU quantity calculators."""

from __future__ import annotations

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


class TestAwsLambdaSkuQuantities:
    def test_lambda_gb_seconds_formula(self) -> None:
        model = get_aws_pricing_model("Lambda")
        assert model is not None
        resolved = [
            _assumption("executions_per_month", 1_000_000),
            _assumption("avg_execution_duration_ms", 200),
            _assumption("memory_mb", 512),
            _assumption("network_egress_gb", 1.0),
        ]
        result = calculate_aws_sku_quantities(model, resolved)
        assert result.ready
        gb_seconds = next(q for q in result.quantities if q.sku_key == "gb_seconds")
        expected = 1_000_000 * (200 / 1000) * (512 / 1024)
        assert gb_seconds.quantity == expected


class TestAwsS3SkuQuantities:
    def test_s3_combined_requests(self) -> None:
        model = get_aws_pricing_model("S3")
        assert model is not None
        resolved = [
            _assumption("storage_gb", 100),
            _assumption("write_operations", 5000),
            _assumption("read_operations", 15000),
            _assumption("data_egress_gb", 2.0),
        ]
        result = calculate_aws_sku_quantities(model, resolved)
        assert result.ready
        requests = next(q for q in result.quantities if q.sku_key == "requests")
        assert requests.quantity == 20_000


class TestAwsDynamoDBSkuQuantities:
    def test_dynamodb_storage_and_requests(self) -> None:
        model = get_aws_pricing_model("DynamoDB")
        assert model is not None
        resolved = [
            _assumption("storage_gb", 10),
            _assumption("read_requests_per_month", 1_000_000),
            _assumption("write_requests_per_month", 500_000),
            _assumption("billing_mode", "on_demand"),
        ]
        result = calculate_aws_sku_quantities(model, resolved)
        assert result.ready
        storage = next(q for q in result.quantities if q.sku_key == "storage_gb_month")
        reads = next(q for q in result.quantities if q.sku_key == "read_requests")
        assert storage.quantity == 10
        assert reads.quantity == 1_000_000


class TestAwsPlatformSkuQuantities:
    def test_api_gateway_requests(self) -> None:
        model = get_aws_pricing_model("API Gateway")
        assert model is not None
        resolved = [
            _assumption("requests_per_month", 2_000_000),
            _assumption("data_egress_gb", 5.0),
            _assumption("api_type", "HTTP"),
        ]
        result = calculate_aws_sku_quantities(model, resolved)
        assert result.ready
        requests = next(q for q in result.quantities if q.sku_key == "requests")
        assert requests.quantity == 2_000_000

    def test_alb_hours_and_lcu(self) -> None:
        model = get_aws_pricing_model("Application Load Balancer")
        assert model is not None
        resolved = [
            _assumption("hours_per_month", 730),
            _assumption("lcu_hours_per_month", 100),
            _assumption("data_egress_gb", 1.0),
        ]
        result = calculate_aws_sku_quantities(model, resolved)
        assert result.ready
        lb_hours = next(q for q in result.quantities if q.sku_key == "lb_hours")
        lcu_hours = next(q for q in result.quantities if q.sku_key == "lcu_hours")
        assert lb_hours.quantity == 730
        assert lcu_hours.quantity == 100

    def test_secrets_manager_storage_and_api_calls(self) -> None:
        model = get_aws_pricing_model("Secrets Manager")
        assert model is not None
        resolved = [
            _assumption("secrets_count", 5),
            _assumption("api_calls_per_month", 10_000),
        ]
        result = calculate_aws_sku_quantities(model, resolved)
        assert result.ready
        secret_months = next(q for q in result.quantities if q.sku_key == "secret_months")
        api_calls = next(q for q in result.quantities if q.sku_key == "requests")
        assert secret_months.quantity == 5
        assert api_calls.quantity == 10_000
