"""Regression tests for catalog formula generation."""

from __future__ import annotations

from app.pricing_ingestion.data.aws_formulas import formula_for_service as aws_formula_for_service
from app.pricing_ingestion.data.formulas import formula_for_service as gcp_formula_for_service


class TestPricingFormulaFixes:
    def test_aws_appconfig_formula_excludes_experiment_hours(self) -> None:
        roles = [
            "use1_appconfig_deployments",
            "use1_appconfig_experimenthours",
            "requests",
        ]
        formula = aws_formula_for_service("AppConfig", roles)
        assert "use1_appconfig_experimenthours_cost" not in formula
        assert "use1_appconfig_deployments_cost" in formula
        assert "requests_cost" in formula

    def test_gcp_api_gateway_formula_scales_requests_per_million(self) -> None:
        formula = gcp_formula_for_service(
            "ignored-service-id",
            ["requests", "egress"],
            catalog_id="api-gateway",
        )
        assert formula["requests_cost"] == "(requests / 1000000) * skus.requests.unit_price_usd"
        assert "egress_cost" in formula
