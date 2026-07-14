# GCP Pricing Validation Suite

Reference benchmark for the Architecture Planner Google Cloud pricing engine. Re-run after pricing changes and compare output to baselines in `docs/pricing-validation/reports/`.

## Purpose

The validation suite answers four questions for every supported application archetype:

1. **Realism** — Do monthly GCP costs fall within engineering-judgment expected ranges?
2. **Consistency** — Are usage assumptions, free tier deductions, and component totals internally coherent?
3. **Completeness** — Are all billable SKUs priced, or are gaps explicitly reported?
4. **Pipeline quality** — Which pricing pipeline stage needs improvement?

## Pipeline

Each run executes the full production pricing pipeline:

| Stage | Description |
|-------|-------------|
| 1 | Architecture / component input |
| 2 | Usage assumptions (inferred) |
| 3 | Resolved assumptions |
| 4 | Raw SKU quantities |
| 5 | Free tier / included usage deducted |
| 6 | Billable SKU quantities |
| 7 | Catalog price lookup (`gcp_catalog`) |
| 8 | Final SKU cost → component subtotal |

**Inference mode:** Heuristic fallback by default (`GcpUsageModelBuilder` + scale bands). LLM inference: `--inference llm`.

**Catalog:** Benchmark runs use `GcpCatalogTestFixture` (deterministic, CI-friendly). Production uses live synced Firestore `gcp_catalog`.

## How to run

```bash
cd backend

# Coverage inventory (20 syncable catalog services)
python scripts/gcp_pricing_coverage_report.py

# Full validation suite (scenarios x user counts)
python scripts/run_gcp_pricing_validation.py

# Single scenario
python scripts/run_gcp_pricing_validation.py --scenario static_website

# Scenario cost benchmark table
python scripts/benchmark_gcp_scenarios.py

# Five-scenario Excel benchmark (architecture, usage, SKUs, catalog, validation)
python scripts/export_gcp_scenarios_excel.py
python scripts/export_gcp_scenarios_excel.py --mode llm --catalog firestore

# Unit tests
python -m pytest tests/test_gcp_*.py -q
```

## Supported services

All 20 syncable services from the component catalog seed:

API Gateway, BigQuery, Cloud Firestore, Cloud Logging, Cloud Memorystore for Redis, Cloud Monitoring, Cloud Pub/Sub, Cloud Run, Cloud Run Functions, Cloud SQL, Cloud Storage, Cloud Tasks, Cloud Trace, Firebase, Firebase Hosting, Gemini API, Networking, Secret Manager, Vertex AI, Vertex AI Search.

Unsupported mappings (e.g. Stripe, SendGrid) are excluded from catalog sync and return explicit `pricing_status="unsupported"`.

**Looker Studio** is classified as `pricing_status="ui_only"` at $0 with an explanatory note — analytics costs are expected through backing services such as BigQuery, not omitted from the engine.

## Before merging pricing changes

1. Run `python scripts/gcp_pricing_coverage_report.py` — all target services should show `Supported: yes`.
2. Run `python -m pytest tests/test_gcp_*.py tests/test_project_pricing_service.py -q`.
3. Run `python scripts/run_gcp_pricing_validation.py` and review warnings in `docs/pricing-validation/reports/`.
