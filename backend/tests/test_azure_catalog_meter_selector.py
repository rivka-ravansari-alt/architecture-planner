"""Tests for AzureCatalogMeterSelector tier-aware meter selection."""

from __future__ import annotations

from app.pricing.azure.catalog_meter_selector import AzureCatalogMeterSelector
from app.pricing.schemas import UsageAssumption, AssumptionConfidence, AssumptionSource


class TestAzureCatalogMeterSelector:
    def test_selects_hot_lrs_storage_key(self) -> None:
        selector = AzureCatalogMeterSelector()
        doc = {
            "skus": {
                "storage": {"unit_price_usd": 0.02, "usage_unit": "1 GB/Month", "description": "generic"},
                "storage:hot:lrs": {
                    "unit_price_usd": 0.018,
                    "usage_unit": "1 GB/Month",
                    "description": "Hot LRS",
                },
                "storage:cool:lrs": {
                    "unit_price_usd": 0.01,
                    "usage_unit": "1 GB/Month",
                    "description": "Cool LRS",
                },
            }
        }
        resolved = [
            UsageAssumption(
                key="access_tier",
                value="Hot",
                unit="enum",
                source=AssumptionSource.user_provided,
                confidence=AssumptionConfidence.high,
            ),
            UsageAssumption(
                key="redundancy",
                value="LRS",
                unit="enum",
                source=AssumptionSource.user_provided,
                confidence=AssumptionConfidence.high,
            ),
        ]
        price = selector.select(doc, "storage", resolved)
        assert price is not None
        assert price.unit_price_usd == 0.018

    def test_selects_sql_instance_by_tier(self) -> None:
        selector = AzureCatalogMeterSelector()
        doc = {
            "skus": {
                "instance": {"unit_price_usd": 20, "usage_unit": "1/month", "description": "generic"},
                "instance:standard_s1": {
                    "unit_price_usd": 30,
                    "usage_unit": "1/month",
                    "description": "Standard S1",
                },
            }
        }
        resolved = [
            UsageAssumption(
                key="tier",
                value="Standard S1",
                unit="enum",
                source=AssumptionSource.user_provided,
                confidence=AssumptionConfidence.high,
            ),
        ]
        price = selector.select(doc, "instance", resolved)
        assert price is not None
        assert price.unit_price_usd == 30
