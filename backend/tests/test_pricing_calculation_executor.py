"""Unit tests for pricing script execution."""

from __future__ import annotations

import pytest

from app.services.pricing_calculation_executor import (
    PricingCalculationError,
    execute_pricing_script,
)

AWS_LAMBDA_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    requests_per_user_per_month = max(\n"
    "        0,\n"
    "        inputs.get(\"requests_per_user_per_month\", 0)\n"
    "    )\n"
    "    average_execution_time_ms = max(\n"
    "        0,\n"
    "        inputs.get(\"average_execution_time_ms\", 0)\n"
    "    )\n"
    "    memory_mb = min(\n"
    "        10240,\n"
    "        max(128, inputs.get(\"memory_mb\", 128))\n"
    "    )\n"
    "    request_sku = next(sku for sku in skus if sku[\"name\"] == \"Requests\")\n"
    "    compute_sku = next(\n"
    "        sku for sku in skus\n"
    "        if sku[\"name\"] == \"Compute Duration\"\n"
    "    )\n"
    "    monthly_requests = users * requests_per_user_per_month\n"
    "    free_requests = free_tier.get(\"requests\", 0)\n"
    "    billable_requests = max(0, monthly_requests - free_requests)\n"
    "    request_cost = (\n"
    "        billable_requests / 1_000_000\n"
    "    ) * request_sku[\"price_per_million\"]\n"
    "    memory_gb = memory_mb / 1024\n"
    "    execution_seconds = average_execution_time_ms / 1000\n"
    "    compute_gb_seconds = (\n"
    "        monthly_requests * memory_gb * execution_seconds\n"
    "    )\n"
    "    free_compute_gb_seconds = free_tier.get(\"compute_gb_seconds\", 0)\n"
    "    billable_compute_gb_seconds = max(\n"
    "        0,\n"
    "        compute_gb_seconds - free_compute_gb_seconds\n"
    "    )\n"
    "    compute_cost = (\n"
    "        billable_compute_gb_seconds\n"
    "        * compute_sku[\"price_per_gb_second\"]\n"
    "    )\n"
    "    estimated_price = request_cost + compute_cost\n"
    "    return round(estimated_price, 2)"
)


def test_execute_pricing_script_returns_monthly_total():
    result = execute_pricing_script(
        AWS_LAMBDA_SCRIPT,
        inputs={
            "users": 1000,
            "requests_per_user_per_month": 120,
            "average_execution_time_ms": 200,
            "memory_mb": 256,
        },
        skus=[
            {"name": "Requests", "price_per_million": 0.2},
            {"name": "Compute Duration", "price_per_gb_second": 0.0000166667},
        ],
        free_tier={"requests": 1_000_000, "compute_gb_seconds": 400_000},
    )

    assert isinstance(result.monthly_price, float)
    assert result.monthly_price >= 0
    assert result.details is not None


def test_execute_pricing_script_builds_lambda_details_breakdown():
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
        to_know={
            "llm": [
                "requests_per_user_per_month",
                "average_execution_time_ms",
                "memory_mb",
            ],
            "static": ["users"],
        },
    )

    assert result.monthly_price == 0.0
    assert result.details.inputs == {
        "users": 1000,
        "requests_per_user_per_month": 120,
        "average_execution_time_ms": 200,
        "memory_mb": 512,
    }
    assert result.details.derived["monthly_requests"] == 120000
    assert result.details.derived["compute_gb_seconds"] == 12000
    assert result.details.free_tier == {
        "requests": 1_000_000,
        "compute_gb_seconds": 400_000,
    }
    assert result.details.billable == {
        "requests": 0,
        "compute_gb_seconds": 0,
    }
    assert {line.label for line in result.details.formula_breakdown} == {
        "Request",
        "Compute",
    }
    assert result.details.monthly_price == 0.0


def test_execute_pricing_script_accepts_structured_dict_result():
    script = (
        "def calculate_price(inputs, skus, free_tier):\n"
        "    return {\n"
        "        \"monthly_price\": 1.25,\n"
        "        \"inputs\": {\"users\": inputs.get(\"users\", 0)},\n"
        "        \"derived\": {\"requests_per_month\": 100},\n"
        "        \"free_tier\": {\"requests\": 1000},\n"
        "        \"billable\": {\"requests\": 0},\n"
        "        \"formula_breakdown\": [\n"
        "            {\"label\": \"Requests\", \"formula\": \"0 * 0.2\", \"amount\": 1.25}\n"
        "        ],\n"
        "    }"
    )

    result = execute_pricing_script(
        script,
        inputs={"users": 10},
        skus=[],
        free_tier={},
    )

    assert result.monthly_price == 1.25
    assert result.details.inputs["users"] == 10
    assert result.details.derived["requests_per_month"] == 100
    assert result.details.billable["requests"] == 0
    assert result.details.formula_breakdown[0].amount == 1.25


def test_execute_pricing_script_rejects_missing_function():
    with pytest.raises(PricingCalculationError, match="calculate_price"):
        execute_pricing_script("x = 1", inputs={}, skus=[], free_tier={})


def test_execute_pricing_script_allows_value_error_in_script():
    script = (
        "def calculate_price(inputs, skus, free_tier):\n"
        "    raise ValueError(\"no matching sku\")"
    )

    with pytest.raises(PricingCalculationError, match="no matching sku"):
        execute_pricing_script(script, inputs={}, skus=[], free_tier={})


AZURE_COSMOS_DB_SERVERLESS_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    valid_modes = {\"Serverless\", \"Provisioned Throughput\", \"Autoscale\"}\n"
    "    capacity_mode = inputs.get(\"capacity_mode\")\n"
    "    if capacity_mode not in valid_modes:\n"
    "        raise ValueError(f\"Invalid capacity_mode: {capacity_mode!r}\")\n"
    "    database_storage_gb = max(0, inputs.get(\"database_storage_gb\", 0))\n"
    "    selected_sku = next(\n"
    "        sku for sku in skus if sku[\"name\"] == capacity_mode\n"
    "    )\n"
    "    free_storage_gb = free_tier.get(\"database_storage_gb\", 0)\n"
    "    billable_storage_gb = max(0, database_storage_gb - free_storage_gb)\n"
    "    storage_cost = (\n"
    "        billable_storage_gb * selected_sku[\"storage_price_per_gb_month\"]\n"
    "    )\n"
    "    if selected_sku[\"name\"] == \"Serverless\":\n"
    "        request_units_per_month = inputs.get(\"request_units_per_month\")\n"
    "        if request_units_per_month is None or request_units_per_month <= 0:\n"
    "            raise ValueError(\n"
    "                \"request_units_per_month is required for Serverless capacity mode.\"\n"
    "            )\n"
    "        price_per_million_ru = selected_sku.get(\"price_per_million_ru\")\n"
    "        if price_per_million_ru is None:\n"
    "            price_per_million_ru = 0.25\n"
    "        request_cost = (\n"
    "            request_units_per_month / 1_000_000\n"
    "        ) * price_per_million_ru\n"
    "        return round(request_cost + storage_cost, 2)\n"
    "    required_ru_per_second = inputs.get(\"required_ru_per_second\")\n"
    "    if required_ru_per_second is None or required_ru_per_second < 0:\n"
    "        raise ValueError(\"required_ru_per_second is required.\")\n"
    "    return round(storage_cost, 2)"
)


def test_execute_pricing_script_supports_azure_cosmos_db_serverless():
    result = execute_pricing_script(
        AZURE_COSMOS_DB_SERVERLESS_SCRIPT,
        inputs={
            "capacity_mode": "Serverless",
            "request_units_per_month": 2_000_000,
            "database_storage_gb": 10,
        },
        skus=[
            {
                "name": "Serverless",
                "price_per_million_ru": 0.25,
                "storage_price_per_gb_month": 0.25,
            }
        ],
        free_tier={"database_storage_gb": 25},
    )

    assert result.monthly_price == 0.5


def test_execute_pricing_script_rejects_invalid_capacity_mode():
    with pytest.raises(PricingCalculationError, match="Invalid capacity_mode"):
        execute_pricing_script(
            AZURE_COSMOS_DB_SERVERLESS_SCRIPT,
            inputs={"capacity_mode": 1.0, "database_storage_gb": 5},
            skus=[
                {
                    "name": "Serverless",
                    "price_per_million_ru": 0.25,
                    "storage_price_per_gb_month": 0.25,
                }
            ],
            free_tier={"database_storage_gb": 25},
        )


AWS_COGNITO_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    authentication_methods = inputs.get(\"authentication_methods\", []) or []\n"
    "    sms_per_user = max(0, inputs.get(\"sms_verifications_per_user_per_month\", 0))\n"
    "    mau_sku = next(sku for sku in skus if sku[\"name\"] == \"Monthly Active User\")\n"
    "    sms_sku = next(sku for sku in skus if sku[\"name\"] == \"SMS Verification\")\n"
    "    free_mau = free_tier.get(\"monthly_active_users\", 0)\n"
    "    billable_mau = max(0, users - free_mau)\n"
    "    mau_cost = billable_mau * mau_sku[\"price_per_mau\"]\n"
    "    sms_cost = 0\n"
    "    if \"sms\" in authentication_methods:\n"
    "        monthly_sms = users * sms_per_user\n"
    "        sms_cost = monthly_sms * sms_sku[\"price_per_sms\"]\n"
    "    estimated_price = mau_cost + sms_cost\n"
    "    return round(estimated_price, 2)"
)

AWS_COGNITO_SKUS = [
    {
        "name": "Monthly Active User",
        "unit": "monthly_active_user",
        "price_per_mau": 0.015,
    },
    {
        "name": "SMS Verification",
        "unit": "sms",
        "price_per_sms": 0.05,
    },
]


def test_execute_pricing_script_supports_aws_cognito_mau():
    result = execute_pricing_script(
        AWS_COGNITO_SCRIPT,
        inputs={
            "users": 12_000,
            "authentication_methods": ["email", "google"],
            "sms_verifications_per_user_per_month": 0,
        },
        skus=AWS_COGNITO_SKUS,
        free_tier={"monthly_active_users": 10_000},
    )

    assert result.monthly_price == 30.0


def test_execute_pricing_script_supports_aws_cognito_sms():
    result = execute_pricing_script(
        AWS_COGNITO_SCRIPT,
        inputs={
            "users": 12_000,
            "authentication_methods": ["email", "sms"],
            "sms_verifications_per_user_per_month": 1,
        },
        skus=AWS_COGNITO_SKUS,
        free_tier={"monthly_active_users": 10_000},
    )

    # MAU: 2_000 * 0.015 = 30; SMS: 12_000 * 0.05 = 600
    assert result.monthly_price == 630.0


AZURE_ENTRA_ID_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    authentication_methods = inputs.get(\"authentication_methods\", []) or []\n"
    "    sms_per_user = max(0, inputs.get(\"sms_verifications_per_user_per_month\", 0))\n"
    "    mau_sku = next(sku for sku in skus if sku[\"name\"] == \"Monthly Active User\")\n"
    "    sms_sku = next(sku for sku in skus if sku[\"name\"] == \"SMS Verification\")\n"
    "    free_mau = free_tier.get(\"monthly_active_users\", 0)\n"
    "    billable_mau = max(0, users - free_mau)\n"
    "    mau_cost = billable_mau * mau_sku[\"price_per_mau\"]\n"
    "    sms_cost = 0\n"
    "    if \"sms\" in authentication_methods:\n"
    "        monthly_sms = users * sms_per_user\n"
    "        free_sms = free_tier.get(\"sms_per_month_estimate\", 0)\n"
    "        billable_sms = max(0, monthly_sms - free_sms)\n"
    "        sms_cost = billable_sms * sms_sku[\"price_per_sms\"]\n"
    "    return round(mau_cost + sms_cost, 2)"
)

AZURE_ENTRA_ID_SKUS = [
    {
        "name": "Monthly Active User",
        "unit": "monthly_active_user",
        "price_per_mau": 0.03,
    },
    {
        "name": "SMS Verification",
        "unit": "sms",
        "price_per_sms": 0.05,
    },
]

AZURE_ENTRA_ID_FREE_TIER = {
    "monthly_active_users": 50_000,
    "sms_per_day": 10,
    "sms_per_month_estimate": 300,
}


def test_execute_pricing_script_supports_azure_entra_id_mau():
    result = execute_pricing_script(
        AZURE_ENTRA_ID_SCRIPT,
        inputs={
            "users": 55_000,
            "authentication_methods": ["microsoft"],
            "sms_verifications_per_user_per_month": 0,
        },
        skus=AZURE_ENTRA_ID_SKUS,
        free_tier=AZURE_ENTRA_ID_FREE_TIER,
    )

    assert result.monthly_price == 150.0


def test_execute_pricing_script_supports_azure_entra_id_sms():
    result = execute_pricing_script(
        AZURE_ENTRA_ID_SCRIPT,
        inputs={
            "users": 55_000,
            "authentication_methods": ["sms"],
            "sms_verifications_per_user_per_month": 1,
        },
        skus=AZURE_ENTRA_ID_SKUS,
        free_tier=AZURE_ENTRA_ID_FREE_TIER,
    )

    # MAU: 5_000 * 0.03 = 150; SMS: (55_000 - 300) * 0.05 = 2_735
    assert result.monthly_price == 2_885.0


GCP_FIREBASE_AUTH_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    authentication_methods = inputs.get(\"authentication_methods\", []) or []\n"
    "    sms_per_user = max(\n"
    "        0,\n"
    "        inputs.get(\"sms_verifications_per_user_per_month\", 0)\n"
    "    )\n"
    "    free_mau = free_tier.get(\"monthly_active_users\", 0)\n"
    "    remaining_mau = max(0, users - free_mau)\n"
    "    mau_cost = 0\n"
    "    mau_tiers = sorted(\n"
    "        [sku for sku in skus if \"price_per_mau\" in sku],\n"
    "        key=lambda sku: sku[\"from_mau\"]\n"
    "    )\n"
    "    for tier in mau_tiers:\n"
    "        if remaining_mau <= 0:\n"
    "            break\n"
    "        tier_start = tier[\"from_mau\"]\n"
    "        tier_end = tier[\"to_mau\"]\n"
    "        if tier_end is None:\n"
    "            tier_capacity = remaining_mau\n"
    "        else:\n"
    "            tier_capacity = tier_end - tier_start\n"
    "        tier_usage = min(remaining_mau, tier_capacity)\n"
    "        mau_cost += tier_usage * tier[\"price_per_mau\"]\n"
    "        remaining_mau -= tier_usage\n"
    "    sms_cost = 0\n"
    "    if \"sms\" in authentication_methods:\n"
    "        sms_sku = next(\n"
    "            sku for sku in skus if sku[\"name\"] == \"SMS Verification\"\n"
    "        )\n"
    "        monthly_sms = users * sms_per_user\n"
    "        free_sms = free_tier.get(\"sms_per_month_estimate\", 0)\n"
    "        billable_sms = max(0, monthly_sms - free_sms)\n"
    "        sms_cost = billable_sms * sms_sku[\"price_per_sms\"]\n"
    "    return round(mau_cost + sms_cost, 2)"
)

GCP_FIREBASE_AUTH_SKUS = [
    {
        "name": "Tier 1 MAU 50K-100K",
        "from_mau": 50_000,
        "to_mau": 100_000,
        "price_per_mau": 0.0055,
    },
    {
        "name": "Tier 1 MAU 100K-1M",
        "from_mau": 100_000,
        "to_mau": 1_000_000,
        "price_per_mau": 0.0046,
    },
    {
        "name": "Tier 1 MAU 1M-10M",
        "from_mau": 1_000_000,
        "to_mau": 10_000_000,
        "price_per_mau": 0.0032,
    },
    {
        "name": "Tier 1 MAU 10M+",
        "from_mau": 10_000_000,
        "to_mau": None,
        "price_per_mau": 0.0025,
    },
    {
        "name": "SMS Verification",
        "unit": "sms",
        "price_per_sms": 0.05,
        "note": (
            "Average estimated SMS price. "
            "Actual price depends on destination country."
        ),
    },
]

GCP_FIREBASE_AUTH_FREE_TIER = {
    "monthly_active_users": 50_000,
    "sms_per_day": 10,
    "sms_per_month_estimate": 300,
}


def test_execute_pricing_script_supports_gcp_firebase_auth_tiers():
    result = execute_pricing_script(
        GCP_FIREBASE_AUTH_SCRIPT,
        inputs={
            "users": 120_000,
            "authentication_methods": ["email", "google"],
            "sms_verifications_per_user_per_month": 0,
        },
        skus=GCP_FIREBASE_AUTH_SKUS,
        free_tier=GCP_FIREBASE_AUTH_FREE_TIER,
    )

    assert result.monthly_price == pytest.approx(367.0)


def test_execute_pricing_script_supports_gcp_firebase_auth_free_tier():
    result = execute_pricing_script(
        GCP_FIREBASE_AUTH_SCRIPT,
        inputs={
            "users": 40_000,
            "authentication_methods": ["email"],
            "sms_verifications_per_user_per_month": 0,
        },
        skus=GCP_FIREBASE_AUTH_SKUS,
        free_tier=GCP_FIREBASE_AUTH_FREE_TIER,
    )

    assert result.monthly_price == 0.0


def test_execute_pricing_script_supports_gcp_firebase_auth_sms():
    result = execute_pricing_script(
        GCP_FIREBASE_AUTH_SCRIPT,
        inputs={
            "users": 40_000,
            "authentication_methods": ["sms"],
            "sms_verifications_per_user_per_month": 1,
        },
        skus=GCP_FIREBASE_AUTH_SKUS,
        free_tier=GCP_FIREBASE_AUTH_FREE_TIER,
    )

    # MAU free tier covers users; SMS: (40_000 - 300) * 0.05 = 1_985
    assert result.monthly_price == 1_985.0


AWS_SNS_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    channel_count = max(0, inputs.get(\"notification_channel_count\", 0))\n"
    "    if channel_count == 0:\n"
    "        return 0.0\n"
    "    users = max(0, inputs.get(\"users\", 0))\n"
    "    notifications_per_user_per_month = max(\n"
    "        0, inputs.get(\"notifications_per_user_per_month\", 0)\n"
    "    )\n"
    "    notifications = users * notifications_per_user_per_month\n"
    "    publish_sku = next(s for s in skus if s[\"name\"] == \"Publish Requests\")\n"
    "    delivery_sku = next(\n"
    "        s for s in skus if s[\"name\"] == \"Mobile Push Deliveries\"\n"
    "    )\n"
    "    billable_publish = max(\n"
    "        0, notifications - free_tier.get(\"publish_requests\", 0)\n"
    "    )\n"
    "    billable_deliveries = max(\n"
    "        0, notifications - free_tier.get(\"mobile_push_deliveries\", 0)\n"
    "    )\n"
    "    publish_cost = (\n"
    "        billable_publish / 1_000_000\n"
    "    ) * publish_sku[\"price_per_million\"]\n"
    "    delivery_cost = (\n"
    "        billable_deliveries / 1_000_000\n"
    "    ) * delivery_sku[\"price_per_million\"]\n"
    "    return round(publish_cost + delivery_cost, 2)"
)


def test_execute_pricing_script_supports_aws_sns_notifications():
    result = execute_pricing_script(
        AWS_SNS_SCRIPT,
        inputs={
            "users": 1000,
            "notifications_per_user_per_month": 2000,
            "notification_channel_count": 2,
        },
        skus=[
            {
                "name": "Publish Requests",
                "unit": "1000000_requests",
                "price_per_million": 0.50,
            },
            {
                "name": "Mobile Push Deliveries",
                "unit": "1000000_notifications",
                "price_per_million": 0.50,
            },
        ],
        free_tier={
            "publish_requests": 1_000_000,
            "mobile_push_deliveries": 1_000_000,
        },
    )

    assert result.monthly_price == 1.0


def test_execute_pricing_script_returns_zero_when_no_notification_channels():
    result = execute_pricing_script(
        AWS_SNS_SCRIPT,
        inputs={
            "users": 1000,
            "notifications_per_user_per_month": 2000,
            "notification_channel_count": 0,
        },
        skus=[
            {
                "name": "Publish Requests",
                "unit": "1000000_requests",
                "price_per_million": 0.50,
            },
            {
                "name": "Mobile Push Deliveries",
                "unit": "1000000_notifications",
                "price_per_million": 0.50,
            },
        ],
        free_tier={
            "publish_requests": 1_000_000,
            "mobile_push_deliveries": 1_000_000,
        },
    )

    assert result.monthly_price == 0.0


AZURE_COSMOS_DB_SCRIPT = (
    "def calculate_price(inputs, skus, free_tier):\n"
    "    import math\n"
    "    capacity_mode = inputs.get(\"capacity_mode\", \"Provisioned Throughput\")\n"
    "    database_storage_gb = max(0, inputs.get(\"database_storage_gb\", 0))\n"
    "    selected_sku = next(\n"
    "        sku for sku in skus if sku[\"name\"] == capacity_mode\n"
    "    )\n"
    "    billable_storage_gb = max(0, database_storage_gb - free_tier.get(\"database_storage_gb\", 0))\n"
    "    storage_cost = (\n"
    "        billable_storage_gb * selected_sku[\"storage_price_per_gb_month\"]\n"
    "    )\n"
    "    required_ru_per_second = max(0, inputs.get(\"required_ru_per_second\", 250))\n"
    "    billable_ru_per_second = max(\n"
    "        0,\n"
    "        required_ru_per_second - free_tier.get(\"throughput_ru_per_second\", 0)\n"
    "    )\n"
    "    throughput_units = math.ceil(\n"
    "        billable_ru_per_second / selected_sku[\"throughput_unit_ru_per_second\"]\n"
    "    )\n"
    "    throughput_cost = (\n"
    "        throughput_units\n"
    "        * selected_sku[\"price_per_100_ru_hour\"]\n"
    "        * 730\n"
    "    )\n"
    "    return round(throughput_cost + storage_cost, 2)"
)


def test_execute_pricing_script_allows_math_import_for_azure_cosmos_db():
    result = execute_pricing_script(
        AZURE_COSMOS_DB_SCRIPT,
        inputs={
            "capacity_mode": "Provisioned Throughput",
            "required_ru_per_second": 250,
            "database_storage_gb": 10,
        },
        skus=[
            {
                "name": "Provisioned Throughput",
                "throughput_unit_ru_per_second": 100,
                "price_per_100_ru_hour": 0.008,
                "storage_price_per_gb_month": 0.25,
            }
        ],
        free_tier={"database_storage_gb": 25, "throughput_ru_per_second": 1000},
    )

    assert result.monthly_price == 0.0

