"""Tests for entity/category storage model inference."""

from __future__ import annotations

import pytest

from app.core.exceptions import AIValidationError
from app.pricing.schemas import AssumptionSource
from app.pricing.usage.scaling import scale_behavioral_assumptions
from app.pricing.usage.storage_model import (
    backup_storage_gb_per_user,
    entity_storage_gb_per_user,
    inject_rds_storage_into_behavioral,
    inject_s3_storage_into_behavioral,
    parse_rds_storage_model,
    parse_s3_storage_model,
)
from app.pricing.schemas import UsageAssumption, AssumptionConfidence


class TestEntityStorageCalculation:
    def test_singleton_profile_is_tiny(self) -> None:
        gb = entity_storage_gb_per_user(
            records_per_user_per_month=1,
            average_record_size_kb=2,
            retention_months=120,
        )
        assert gb < 0.01

    def test_event_history_scales_with_retention(self) -> None:
        low = entity_storage_gb_per_user(
            records_per_user_per_month=30,
            average_record_size_kb=1,
            retention_months=3,
        )
        high = entity_storage_gb_per_user(
            records_per_user_per_month=30,
            average_record_size_kb=1,
            retention_months=12,
        )
        assert high > low

    def test_backup_derived_from_database_and_retention(self) -> None:
        db = 0.1
        backup = backup_storage_gb_per_user(db, backup_retention_days=7)
        assert backup == pytest.approx(db * 7 / 30, rel=1e-3)


class TestRdsStorageModel:
    def test_parses_entities_and_sums_storage(self) -> None:
        derivation = parse_rds_storage_model(
            {
                "entities": [
                    {
                        "entity": "user_profile",
                        "records_per_user_per_month": 1,
                        "average_record_size_kb": 2,
                        "retention_months": 120,
                        "reasoning": "One profile row per user.",
                    },
                    {
                        "entity": "history_events",
                        "records_per_user_per_month": 60,
                        "average_record_size_kb": 0.5,
                        "retention_months": 6,
                        "reasoning": "Daily exercise completions.",
                    },
                ],
                "backup_retention_days": 7,
            },
            component_id="database",
        )
        assert derivation.storage_gb_per_user > 0
        assert derivation.storage_gb_per_user < 0.05
        assert derivation.backup_storage_gb_per_user < derivation.storage_gb_per_user

    def test_rejects_missing_storage_model_entities(self) -> None:
        with pytest.raises(AIValidationError, match="entities"):
            parse_rds_storage_model({}, component_id="database")


class TestS3StorageModel:
    def test_static_and_per_user_categories(self) -> None:
        derivation = parse_s3_storage_model(
            {
                "categories": [
                    {
                        "category": "static_assets",
                        "scaling": "static",
                        "total_storage_gb": 0.5,
                        "writes_per_user_per_month": 0,
                        "reads_per_user_per_month": 30,
                        "average_object_size_kb": 50,
                        "reasoning": "Shared UI assets.",
                    },
                    {
                        "category": "generated_files",
                        "scaling": "per_user",
                        "storage_gb_per_user": 0.002,
                        "writes_per_user_per_month": 1,
                        "reads_per_user_per_month": 5,
                        "average_object_size_kb": 32,
                        "reasoning": "Small export files.",
                    },
                ]
            },
            component_id="files",
            file_upload=False,
        )
        assert derivation.static_storage_gb == 0.5
        assert derivation.storage_gb_per_user == pytest.approx(0.002)

    def test_zeros_upload_categories_when_file_upload_false(self) -> None:
        derivation = parse_s3_storage_model(
            {
                "categories": [
                    {
                        "category": "static_assets",
                        "scaling": "static",
                        "total_storage_gb": 0.2,
                        "writes_per_user_per_month": 0,
                        "reads_per_user_per_month": 10,
                        "average_object_size_kb": 40,
                        "reasoning": "Static.",
                    },
                    {
                        "category": "user_uploads",
                        "scaling": "per_user",
                        "storage_gb_per_user": 0.5,
                        "writes_per_user_per_month": 2,
                        "reads_per_user_per_month": 2,
                        "average_object_size_kb": 0,
                        "reasoning": "LLM mistake — should be zeroed.",
                    },
                ]
            },
            component_id="files",
            file_upload=False,
        )
        assert derivation.storage_gb_per_user == 0.0
        assert derivation.static_storage_gb == 0.2


class TestStorageScalingIntegration:
    def test_s3_static_storage_not_scaled_by_users(self) -> None:
        behavioral: dict[str, UsageAssumption] = {}
        config: dict[str, UsageAssumption] = {}
        inject_s3_storage_into_behavioral(
            behavioral,
            config,
            parse_s3_storage_model(
                {
                    "categories": [
                        {
                            "category": "static_assets",
                            "scaling": "static",
                            "total_storage_gb": 1.0,
                            "writes_per_user_per_month": 0,
                            "reads_per_user_per_month": 10,
                            "average_object_size_kb": 40,
                            "reasoning": "Static.",
                        },
                        {
                            "category": "generated_files",
                            "scaling": "per_user",
                            "storage_gb_per_user": 0.01,
                            "writes_per_user_per_month": 1,
                            "reads_per_user_per_month": 2,
                            "average_object_size_kb": 20,
                            "reasoning": "Per user.",
                        },
                    ]
                },
                component_id="files",
                file_upload=False,
            ),
        )
        scaled = scale_behavioral_assumptions(
            "S3",
            behavioral=behavioral,
            config=config,
            expected_users=1000,
        )
        assert scaled["storage_gb"].value == pytest.approx(11.0, rel=1e-2)

    def test_rds_scales_entity_sum(self) -> None:
        behavioral: dict[str, UsageAssumption] = {}
        inject_rds_storage_into_behavioral(
            behavioral,
            parse_rds_storage_model(
                {
                    "entities": [
                        {
                            "entity": "user_profile",
                            "records_per_user_per_month": 1,
                            "average_record_size_kb": 2,
                            "retention_months": 120,
                            "reasoning": "Profile.",
                        }
                    ],
                    "backup_retention_days": 7,
                },
                component_id="database",
            ),
        )
        scaled = scale_behavioral_assumptions(
            "RDS",
            behavioral=behavioral,
            config={
                "instance_class": UsageAssumption(
                    key="instance_class",
                    value="db.t3.micro",
                    unit="enum",
                    source=AssumptionSource.inferred,
                    confidence=AssumptionConfidence.high,
                    reasoning="MVP.",
                ),
                "hours_per_month": UsageAssumption(
                    key="hours_per_month",
                    value=730,
                    unit="hours/month",
                    source=AssumptionSource.inferred,
                    confidence=AssumptionConfidence.high,
                    reasoning="Always on.",
                ),
            },
            expected_users=1000,
        )
        assert scaled["storage_gb"].value < 10
        assert scaled["backup_storage_gb"].value < scaled["storage_gb"].value
