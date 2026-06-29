"""Tests for the Cloud Run Job pricing sync entrypoint."""

from __future__ import annotations

from unittest.mock import patch

from app.config.params import PRICE_IMPORT_STATUS_COMPLETED, PRICE_IMPORT_STATUS_FAILED
from app.jobs import pricing_sync_job
from app.pricing_ingestion.schemas.sync import ProviderPricingSyncResponse


def _sync_response(*, status: str) -> ProviderPricingSyncResponse:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return ProviderPricingSyncResponse(
        provider="gcp",
        import_run_id="run-1",
        status=status,
        started_at=now,
        ended_at=now,
        services_total=1,
        services_succeeded=1 if status != PRICE_IMPORT_STATUS_FAILED else 0,
        services_failed=1 if status == PRICE_IMPORT_STATUS_FAILED else 0,
        skus_upserted=0,
    )


def test_main_exits_zero_on_success():
    with patch.object(
        pricing_sync_job,
        "run_pricing_sync",
        return_value=0,
    ) as run_sync:
        assert pricing_sync_job.main(["--provider", "gcp"]) == 0
    run_sync.assert_called_once_with("gcp")


def test_main_exits_nonzero_on_failure():
    with patch.object(pricing_sync_job, "run_pricing_sync", return_value=1):
        assert pricing_sync_job.main(["--provider", "aws"]) == 1


def test_run_pricing_sync_returns_exit_code(monkeypatch):
    def fake_build_orchestrator(_db):
        class FakeOrchestrator:
            def sync(self, _request, *, triggered_by=None):
                assert triggered_by == pricing_sync_job.JOB_PRINCIPAL
                return _sync_response(status=PRICE_IMPORT_STATUS_COMPLETED)

        return FakeOrchestrator()

    monkeypatch.setattr(pricing_sync_job, "init_db", lambda: None)
    monkeypatch.setattr(pricing_sync_job, "build_pricing_sync_orchestrator", fake_build_orchestrator)

    assert pricing_sync_job.run_pricing_sync("all") == 0


def test_run_pricing_sync_failed_status_returns_one(monkeypatch):
    def fake_build_orchestrator(_db):
        class FakeOrchestrator:
            def sync(self, _request, *, triggered_by=None):
                return _sync_response(status=PRICE_IMPORT_STATUS_FAILED)

        return FakeOrchestrator()

    monkeypatch.setattr(pricing_sync_job, "init_db", lambda: None)
    monkeypatch.setattr(pricing_sync_job, "build_pricing_sync_orchestrator", fake_build_orchestrator)

    assert pricing_sync_job.run_pricing_sync("gcp") == 1


def test_triggered_by_includes_cloud_run_execution(monkeypatch):
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", "exec-abc")

    captured: dict[str, str | None] = {}

    def fake_build_orchestrator(_db):
        class FakeOrchestrator:
            def sync(self, _request, *, triggered_by=None):
                captured["triggered_by"] = triggered_by
                return _sync_response(status=PRICE_IMPORT_STATUS_COMPLETED)

        return FakeOrchestrator()

    monkeypatch.setattr(pricing_sync_job, "init_db", lambda: None)
    monkeypatch.setattr(pricing_sync_job, "build_pricing_sync_orchestrator", fake_build_orchestrator)

    pricing_sync_job.run_pricing_sync("gcp")
    assert captured["triggered_by"] == "cloud-run-job:exec-abc"
