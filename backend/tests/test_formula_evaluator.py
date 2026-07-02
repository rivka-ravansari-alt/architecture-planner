"""Tests for pricing formula evaluation."""

from __future__ import annotations

import pytest

from app.services.pricing.formula_evaluator import FormulaEvaluator


def test_linear_formula_uses_inferred_quantity_for_slug_sku_roles():
    evaluator = FormulaEvaluator()
    formula = {
        "use1_amplifywaf_cost": "use1_amplifywaf * skus.use1_amplifywaf.unit_price_usd",
        "total": "use1_amplifywaf_cost",
    }
    skus = {
        "use1_amplifywaf": {
            "sku_id": "waf-1",
            "unit_price_usd": 0.00001,
        }
    }
    usage = {"monthly_requests": 10_000.0}

    total, terms = evaluator.evaluate_formula(formula, usage=usage, skus=skus)

    assert total == pytest.approx(0.1)
    assert terms["use1_amplifywaf_cost"] == pytest.approx(0.1)


def test_storage_slug_role_maps_to_storage_gib():
    evaluator = FormulaEvaluator()
    formula = {
        "p6_lrs_cost": "p6_lrs * skus.p6_lrs.unit_price_usd",
        "total": "p6_lrs_cost",
    }
    skus = {"p6_lrs": {"sku_id": "blob", "unit_price_usd": 0.02}}
    usage = {"storage_gib": 100.0}

    total, _terms = evaluator.evaluate_formula(formula, usage=usage, skus=skus)

    assert total == pytest.approx(2.0)
