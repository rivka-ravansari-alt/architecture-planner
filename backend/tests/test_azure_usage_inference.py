"""Tests for Azure usage model builder and inference engine."""

from __future__ import annotations

from app.models import Project
from app.pricing.azure.heuristic_usage_inference import HeuristicUsageInference
from app.pricing.azure.usage_inference import AzureUsageInferenceEngine
from app.pricing.azure.usage_model_builder import AzureUsageModelBuilder
from app.pricing.schemas import AssumptionConfidence, AssumptionSource
from app.schemas.domain import MappedComponent


def _project(expected_users: str = "100", stage: str = "mvp") -> Project:
    return Project(name="Test", description="", expected_users=expected_users, stage=stage)


def _component(
    *,
    key: str = "api",
    component_type: str = "service",
    azure: str = "Functions",
    optional: bool = False,
) -> MappedComponent:
    return MappedComponent(
        key=key,
        name=key,
        component_type=component_type,
        reason="",
        category="core",
        optional=optional,
        order=0,
        cloud={"aws": "Lambda", "gcp": "Cloud Run", "azure": azure},
    )


class TestAzureUsageModelBuilder:
    def test_user_band_changes_service_traffic(self) -> None:
        builder = AzureUsageModelBuilder()
        profile_100 = builder.build_profile(_project("100"), [_component()])
        profile_10k = builder.build_profile(_project("10000"), [_component()])
        usage_100 = builder.build_for_component(profile_100, _component(), "Azure Functions")
        usage_10k = builder.build_for_component(profile_10k, _component(), "Azure Functions")
        assert usage_10k["executions_per_month"] > usage_100["executions_per_month"] * 5

    def test_optional_component_reduces_usage(self) -> None:
        builder = AzureUsageModelBuilder()
        profile = builder.build_profile(
            _project(),
            [_component(optional=False), _component(key="opt", optional=True)],
        )
        required = builder.build_for_component(
            profile,
            _component(optional=False),
            "Azure Functions",
        )
        optional = builder.build_for_component(
            profile,
            _component(key="opt", optional=True),
            "Azure Functions",
        )
        assert optional["executions_per_month"] < required["executions_per_month"]

    def test_file_upload_increases_object_storage(self) -> None:
        builder = AzureUsageModelBuilder()
        profile = builder.build_profile(
            _project(),
            [_component(component_type="object_storage", azure="Blob Storage")],
            feature_flags={"file_upload": True},
        )
        usage = builder.build_for_component(
            profile,
            _component(component_type="object_storage", azure="Blob Storage"),
            "Azure Blob Storage",
        )
        assert usage["storage_gb"] >= 10
        assert usage["write_operations"] > 0


class TestHeuristicUsageInferenceEngine:
    def test_infers_functions_executions_from_users(self) -> None:
        heuristic = HeuristicUsageInference()
        small = heuristic.infer_component(_project("100"), _component(azure="Functions"))
        large = heuristic.infer_component(_project("10000"), _component(azure="Functions"))
        assert small is not None and large is not None
        small_exec = next(a for a in small.resolved if a.key == "executions_per_month")
        large_exec = next(a for a in large.resolved if a.key == "executions_per_month")
        assert large_exec.value > small_exec.value
        assert small_exec.source == AssumptionSource.inferred
        assert small_exec.confidence == AssumptionConfidence.low

    def test_database_storage_scales_with_users(self) -> None:
        heuristic = HeuristicUsageInference()
        result = heuristic.infer_component(
            _project("1000"),
            _component(component_type="database", azure="SQL Database"),
        )
        assert result is not None
        storage = next(a for a in result.resolved if a.key == "storage_gb")
        assert storage.value >= 8


class TestAzureUsageInferenceEngine:
    def test_heuristic_mode_matches_heuristic_engine(self) -> None:
        engine = AzureUsageInferenceEngine(inference_mode="heuristic")
        results = engine.infer_components(_project(), [_component(azure="Functions")])
        assert len(results) == 1
        assert all(item.source == AssumptionSource.inferred for item in results[0].resolved)
