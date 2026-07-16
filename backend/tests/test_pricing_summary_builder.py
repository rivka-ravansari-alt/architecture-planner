"""Unit tests for concise pricing calculation summaries."""

from __future__ import annotations

from app.services.pricing_calculation_executor import execute_pricing_script
from app.services.pricing_summary_builder import build_calculation_summary
from tests.test_pricing_calculation_executor import AWS_LAMBDA_SCRIPT


def test_build_calculation_summary_for_aws_lambda():
    summary = build_calculation_summary(
        service_id="aws_lambda",
        locals_snapshot={
            "monthly_requests": 120_000,
            "memory_mb": 512,
            "average_execution_time_ms": 200,
            "billable_requests": 0,
            "compute_gb_seconds": 12_000,
            "billable_compute_gb_seconds": 0,
        },
        free_tier={"requests": 1_000_000, "compute_gb_seconds": 400_000},
        monthly_price=0.0,
    )

    assert summary == [
        "Requests: 120,000/month",
        "Memory: 512 MB",
        "Execution: 200 ms",
        "Free tier applied",
        "Price: $0.00",
    ]


def test_build_calculation_summary_for_cloud_sql_package():
    summary = build_calculation_summary(
        service_id="gcp_cloud_sql",
        locals_snapshot={
            "required_cpu": 2,
            "required_ram_gb": 4,
            "required_database_storage_gb": 10,
            "selected_sku": {"name": "Sandbox", "monthly_price": 140},
        },
        free_tier={},
        monthly_price=140.0,
    )

    assert summary == [
        "CPU: 2",
        "RAM: 4 GB",
        "Database: 10 GB",
        "Selected package: Sandbox",
        "Price: $140.00",
    ]


def test_build_calculation_summary_for_s3():
    summary = build_calculation_summary(
        service_id="aws_s3",
        locals_snapshot={
            "storage_gb": 25,
            "read_requests": 50_000,
            "data_transfer_out_gb": 10,
            "billable_transfer_gb": 0,
        },
        free_tier={"data_transfer_out_gb": 100},
        monthly_price=0.0,
    )

    assert summary == [
        "Storage: 25 GB",
        "Monthly reads: 50,000",
        "Free tier applied",
        "Price: $0.00",
    ]


def test_execute_pricing_script_includes_lambda_summary():
    result = execute_pricing_script(
        AWS_LAMBDA_SCRIPT,
        inputs={
            "users": 1000,
            "requests_per_user_per_month": 120,
            "average_execution_time_ms": 200,
            "memory_mb": 512,
        },
        skus=[
            {"name": "Requests", "price_per_million": 0.2},
            {"name": "Compute Duration", "price_per_gb_second": 0.0000166667},
        ],
        free_tier={"requests": 1_000_000, "compute_gb_seconds": 400_000},
        service_id="aws_lambda",
    )

    assert result.calculation_summary == [
        "Requests: 120,000/month",
        "Memory: 512 MB",
        "Execution: 200 ms",
        "Free tier applied",
        "Price: $0.00",
    ]
