"""Tests for global usage model response validation (Step 3)."""

from __future__ import annotations

import pytest

from app.core.exceptions import AIValidationError
from app.validators.global_usage_validator import parse_and_validate, parse_global_usage_model


def test_parse_valid_global_usage_model():
    raw = """
    {
      "usage": {
        "users": {
          "value": 1000,
          "reason": "Matches expected user count for MVP."
        },
        "requests_per_month": {
          "value": 50000,
          "reason": "Moderate API traffic for CRUD workflows."
        }
      }
    }
    """
    result = parse_global_usage_model(raw)
    assert result.usage["users"].value == 1000
    assert result.usage["requests_per_month"].value == 50000


def test_parse_and_validate_requires_exact_parameter_coverage():
    raw = """
    {
      "usage": {
        "users": {
          "value": 1000,
          "reason": "Baseline user count."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="missing from the response"):
        parse_and_validate(raw, ["users", "requests_per_month"])


def test_parse_and_validate_rejects_extra_parameters():
    raw = """
    {
      "usage": {
        "users": {
          "value": 1000,
          "reason": "Baseline user count."
        },
        "requests_per_month": {
          "value": 50000,
          "reason": "Extra parameter."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="unexpected parameters"):
        parse_and_validate(raw, ["users"])


def test_parse_and_validate_rejects_negative_values():
    raw = """
    {
      "usage": {
        "users": {
          "value": -1,
          "reason": "Invalid negative value."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="schema validation"):
        parse_and_validate(raw, ["users"])


def test_parse_and_validate_accepts_capacity_mode_string_enum():
    raw = """
    {
      "usage": {
        "capacity_mode": {
          "value": "Serverless",
          "reason": "MVP traffic fits serverless billing."
        }
      }
    }
    """
    result = parse_and_validate(raw, ["capacity_mode"])
    assert result.usage["capacity_mode"].value == "Serverless"


def test_parse_and_validate_rejects_numeric_capacity_mode():
    raw = """
    {
      "usage": {
        "capacity_mode": {
          "value": 1,
          "reason": "Wrong type."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="string enum"):
        parse_and_validate(raw, ["capacity_mode"])


def test_parse_and_validate_rejects_invalid_capacity_mode_value():
    raw = """
    {
      "usage": {
        "capacity_mode": {
          "value": "Dedicated",
          "reason": "Invalid enum."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="must be one of"):
        parse_and_validate(raw, ["capacity_mode"])


def test_parse_and_validate_accepts_workload_type_string_enum():
    raw = """
    {
      "usage": {
        "workload_type": {
          "value": "Burstable",
          "reason": "MVP traffic fits burstable instances."
        }
      }
    }
    """
    result = parse_and_validate(raw, ["workload_type"])
    assert result.usage["workload_type"].value == "Burstable"


def test_parse_and_validate_rejects_numeric_workload_type():
    raw = """
    {
      "usage": {
        "workload_type": {
          "value": 1,
          "reason": "Wrong type."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="string enum"):
        parse_and_validate(raw, ["workload_type"])


def test_parse_and_validate_rejects_invalid_workload_type_value():
    raw = """
    {
      "usage": {
        "workload_type": {
          "value": "Spot",
          "reason": "Invalid enum."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="must be one of"):
        parse_and_validate(raw, ["workload_type"])


def test_parse_and_validate_allows_omitting_required_ru_for_serverless():
    raw = """
    {
      "usage": {
        "capacity_mode": {
          "value": "Serverless",
          "reason": "Burst traffic fits serverless."
        },
        "request_units_per_user_per_month": {
          "value": 500,
          "reason": "Light document reads/writes."
        }
      }
    }
    """
    result = parse_and_validate(
        raw,
        [
            "capacity_mode",
            "request_units_per_user_per_month",
            "required_ru_per_second",
        ],
    )

    assert result.usage["capacity_mode"].value == "Serverless"
    assert result.usage["request_units_per_user_per_month"].value == 500
    assert result.usage["required_ru_per_second"].value == 0


def test_parse_and_validate_allows_omitting_request_units_for_provisioned():
    raw = """
    {
      "usage": {
        "capacity_mode": {
          "value": "Provisioned Throughput",
          "reason": "Steady traffic needs reserved RU/s."
        },
        "required_ru_per_second": {
          "value": 400,
          "reason": "Peak read/write throughput."
        }
      }
    }
    """
    result = parse_and_validate(
        raw,
        [
            "capacity_mode",
            "request_units_per_user_per_month",
            "required_ru_per_second",
        ],
    )

    assert result.usage["capacity_mode"].value == "Provisioned Throughput"
    assert result.usage["required_ru_per_second"].value == 400
    assert result.usage["request_units_per_user_per_month"].value == 0


def test_parse_and_validate_still_requires_mode_specific_param():
    raw = """
    {
      "usage": {
        "capacity_mode": {
          "value": "Serverless",
          "reason": "Burst traffic fits serverless."
        }
      }
    }
    """
    with pytest.raises(AIValidationError, match="request_units_per_user_per_month"):
        parse_and_validate(
            raw,
            [
                "capacity_mode",
                "request_units_per_user_per_month",
                "required_ru_per_second",
            ],
        )
