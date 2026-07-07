"""Tests for AWS usage inference."""

from __future__ import annotations

from app.models import Project
from app.pricing.aws.usage_inference import AwsUsageInferenceEngine
from app.schemas.domain import MappedComponent


class TestAwsUsageInference:
    def test_heuristic_inference_for_lambda_component(self) -> None:
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
        engine = AwsUsageInferenceEngine()
        inputs = engine.infer_components(project, components)
        assert len(inputs) == 1
        assert inputs[0].cloud_service == "Lambda"
        assert inputs[0].provider == "aws"
        keys = {item.key for item in inputs[0].resolved}
        assert "executions_per_month" in keys
