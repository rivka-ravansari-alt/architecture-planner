"""API schema tests for profile-driven pricing metadata."""



from __future__ import annotations



from app.schemas.project import CostEstimateOut





def test_legacy_cost_estimate_totals_are_not_zeroed_in_schema():

    """Stale totals are recalculated server-side; the schema must not hide them."""

    estimate = CostEstimateOut.model_validate(

        {

            "provider": "gcp",

            "monthly_low": 99999.0,

            "monthly_high": 150000.0,

            "required_monthly_low": 99999.0,

            "required_monthly_high": 150000.0,

            "optional_monthly_low": 5000.0,

            "optional_monthly_high": 8000.0,

            "currency": "USD",

            "notes": "legacy",

            "calculator_version": "",

            "component_breakdown": [],

            "pricing_debug_table": [],

        }

    )

    assert estimate.monthly_low == 99999.0

    assert estimate.required_monthly_high == 150000.0





def test_profile_driven_cost_estimate_preserves_totals_and_profile_id():

    estimate = CostEstimateOut.model_validate(

        {

            "provider": "gcp",

            "monthly_low": 12.0,

            "monthly_high": 18.0,

            "required_monthly_low": 12.0,

            "required_monthly_high": 18.0,

            "optional_monthly_low": 0.0,

            "optional_monthly_high": 0.0,

            "currency": "USD",

            "notes": "profile driven",

            "calculator_version": "baseline_usage_v1",

            "component_breakdown": [

                {

                    "component_key": "service",

                    "component_type": "api",

                    "component_name": "API",

                    "selected_cloud_service": "Cloud Run",

                    "pricing_record_id": "cloud-run",

                    "pricing_record_name": "Cloud Run",

                    "pricing_profile_id": "cloud_run",

                    "pricing_profile_service": "Cloud Run",

                    "pricing_model": "compute_request_based",

                    "expected_users": "100",

                    "usage_assumptions": {"monthly_requests": 1000.0},

                    "sku_lines": [],

                    "final_component_cost": 1.2,

                    "optional": False,

                }

            ],

        }

    )

    assert estimate.calculator_version == "baseline_usage_v1"

    assert estimate.required_monthly_low == 12.0

    assert estimate.component_breakdown[0].pricing_profile_id == "cloud_run"

