"""Tests for automatic stale cost estimate refresh."""

from __future__ import annotations

from app.config.params import (
    CALCULATOR_VERSION_PROFILE_DRIVEN,
    WORKFLOW_STATUS_ARCHITECTURE_APPROVED,
    WORKFLOW_STATUS_DIAGRAMS_GENERATED,
    WORKFLOW_STATUS_PRICING_GENERATED,
)
from app.models import CloudMapping, CostEstimate, ProjectComponent
from app.services.cost_estimate_refresh_service import CostEstimateRefreshService


def _add_component(project, *, key="api", name="API Gateway") -> None:
    component = ProjectComponent(
        key=key,
        name=name,
        component_type="api",
        reason="Handles requests",
        category="core",
        optional=False,
        order=0,
    )
    component.cloud_mapping = CloudMapping(
        aws=["API Gateway"],
        gcp=["Cloud Run"],
        azure=["Azure App Service"],
    )
    project.components.append(component)


def test_needs_refresh_when_calculator_version_missing(db_session, sample_project):
    service = CostEstimateRefreshService(db_session)
    sample_project.workflow_status = WORKFLOW_STATUS_ARCHITECTURE_APPROVED
    _add_component(sample_project)
    sample_project.cost_estimates.append(
        CostEstimate(
            provider="gcp",
            monthly_low=999.0,
            monthly_high=999.0,
            required_monthly_low=999.0,
            required_monthly_high=999.0,
            calculator_version="",
        )
    )
    db_session.commit()

    assert service._needs_refresh(sample_project) is True


def test_ensure_current_estimates_recalculates_stale_legacy(db_session, sample_project, caplog):
    service = CostEstimateRefreshService(db_session)
    sample_project.workflow_status = WORKFLOW_STATUS_ARCHITECTURE_APPROVED
    _add_component(sample_project)
    sample_project.cost_estimates.append(
        CostEstimate(
            provider="gcp",
            monthly_low=99999.0,
            monthly_high=99999.0,
            required_monthly_low=99999.0,
            required_monthly_high=99999.0,
            calculator_version="legacy_v0",
        )
    )
    db_session.commit()

    with caplog.at_level("INFO"):
        refreshed = service.ensure_current_estimates(sample_project)

    assert refreshed.workflow_status == WORKFLOW_STATUS_PRICING_GENERATED
    assert refreshed.cost_estimates
    assert all(
        estimate.calculator_version == CALCULATOR_VERSION_PROFILE_DRIVEN
        for estimate in refreshed.cost_estimates
    )
    assert refreshed.cost_estimates[0].required_monthly_high != 99999.0
    assert "COST_ESTIMATE_STALE_RECALCULATING" in caplog.text
    assert "COST_ESTIMATE_RECALCULATED_SUCCESSFULLY" in caplog.text
    assert "PROFILE_DRIVEN_COST_CALCULATOR_USED" in caplog.text


def test_ensure_current_estimates_skips_current_profile_driven(db_session, sample_project):
    service = CostEstimateRefreshService(db_session)
    sample_project.workflow_status = WORKFLOW_STATUS_PRICING_GENERATED
    _add_component(sample_project)
    sample_project.cost_estimates.append(
        CostEstimate(
            provider="gcp",
            monthly_low=12.0,
            monthly_high=18.0,
            required_monthly_low=12.0,
            required_monthly_high=18.0,
            calculator_version=CALCULATOR_VERSION_PROFILE_DRIVEN,
        )
    )
    db_session.commit()
    original_ids = {estimate.id for estimate in sample_project.cost_estimates}

    refreshed = service.ensure_current_estimates(sample_project)

    assert {estimate.id for estimate in refreshed.cost_estimates} == original_ids


def test_ensure_current_estimates_auto_approves_diagrams_generated(db_session, sample_project):
    service = CostEstimateRefreshService(db_session)
    sample_project.workflow_status = WORKFLOW_STATUS_DIAGRAMS_GENERATED
    _add_component(sample_project)
    db_session.commit()

    refreshed = service.ensure_current_estimates(sample_project)

    assert refreshed.workflow_status == WORKFLOW_STATUS_PRICING_GENERATED
    assert refreshed.cost_estimates
