"""Tests for Azure pricing coverage across component catalog services."""

from __future__ import annotations

from app.config.params import AZURE_CATALOG_SKIP_OPTIONS
from app.data.component_catalog_seed import COMPONENT_CATALOG_SEED
from app.pricing.azure.registry import get_azure_pricing_model, list_azure_pricing_models
from app.pricing.azure.sku_quantities.calculator import _CALCULATORS
from app.pricing.usage.behavioral_models import AZURE_BEHAVIORAL_MODELS


def _catalog_azure_service_names() -> set[str]:
    names: set[str] = set()
    for entry in COMPONENT_CATALOG_SEED:
        for raw in entry.get("azure_options") or []:
            if isinstance(raw, str):
                name = raw.strip()
            elif isinstance(raw, dict):
                name = str(raw.get("name", "")).strip()
            else:
                continue
            if name and name not in AZURE_CATALOG_SKIP_OPTIONS:
                names.add(name)
    return names


class TestAzureCatalogCoverage:
    def test_all_catalog_azure_services_have_pricing_models(self) -> None:
        catalog = _catalog_azure_service_names()
        missing = sorted(name for name in catalog if get_azure_pricing_model(name) is None)
        assert not missing, f"Missing pricing models for: {missing}"

    def test_pricing_engine_has_twenty_three_services(self) -> None:
        models = list_azure_pricing_models()
        assert len(models) == 23

    def test_all_models_have_sku_calculators(self) -> None:
        for model in list_azure_pricing_models():
            assert model.service in _CALCULATORS, model.service

    def test_all_models_have_behavioral_models(self) -> None:
        for model in list_azure_pricing_models():
            assert model.service in AZURE_BEHAVIORAL_MODELS, model.service

    def test_catalog_service_count(self) -> None:
        assert len(_catalog_azure_service_names()) == 23
