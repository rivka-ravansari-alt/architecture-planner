"""Cloud Run Job entrypoint for scheduled pricing catalog sync."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from app.config.params import PRICE_IMPORT_STATUS_FAILED
from app.core.database import SessionLocal, init_db
from app.pricing_ingestion.factory import build_pricing_sync_orchestrator
from app.pricing_ingestion.schemas.sync import PricingProvider, PricingSyncRequest

logger = logging.getLogger(__name__)

JOB_PRINCIPAL = "cloud-run-job"
PROVIDER_CHOICES: tuple[PricingProvider, ...] = ("gcp", "aws", "azure", "all")


def _resolve_triggered_by() -> str:
    execution = os.environ.get("CLOUD_RUN_EXECUTION", "").strip()
    if execution:
        return f"{JOB_PRINCIPAL}:{execution}"
    return JOB_PRINCIPAL


def run_pricing_sync(provider: PricingProvider) -> int:
    """Run pricing sync and return a process exit code (0 = success)."""
    init_db()
    with SessionLocal() as session:
        orchestrator = build_pricing_sync_orchestrator(session)
        result = orchestrator.sync(
            PricingSyncRequest(provider=provider),
            triggered_by=_resolve_triggered_by(),
        )

    logger.info(
        "Pricing sync finished: provider=%s status=%s skus_upserted=%s",
        result.provider,
        result.status,
        result.skus_upserted,
    )
    return 1 if result.status == PRICE_IMPORT_STATUS_FAILED else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync cloud pricing catalogs into Firestore.")
    parser.add_argument(
        "--provider",
        choices=PROVIDER_CHOICES,
        default=os.environ.get("PRICING_SYNC_PROVIDER", "all"),
        help="Cloud provider to sync (default: all, or PRICING_SYNC_PROVIDER env var).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return run_pricing_sync(args.provider)


if __name__ == "__main__":
    sys.exit(main())
