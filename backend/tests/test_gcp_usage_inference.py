"""Tests for GCP usage inference."""

from __future__ import annotations

from app.models import Project
from app.pricing.gcp.usage_inference import GcpUsageInferenceEngine
from app.schemas.domain import MappedComponent


class TestGcpUsageInference:
    def test_heuristic_inference_for_cloud_run_component(self) -> None:
        project = Project(
            name="Test",
            description="",
            stage="mvp",
            expected_users="1000",
        )
        components = [
            MappedComponent(
                key="api",
                name="API",
                component_type="service",
                reason="",
                category="core",
                optional=False,
                order=0,
                cloud={"aws": "Lambda", "azure": "Functions", "gcp": "Cloud Run"},
            )
        ]
        engine = GcpUsageInferenceEngine()
        inputs = engine.infer_components(project, components)
        assert len(inputs) == 1
        assert inputs[0].cloud_service == "Cloud Run"
        assert inputs[0].provider == "gcp"
        keys = {item.key for item in inputs[0].resolved}
        assert "requests_per_month" in keys
