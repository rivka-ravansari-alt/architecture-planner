# Azure Pricing Validation Suite

Reference benchmark for the Architecture Planner Azure pricing engine. **Every future pricing change should be validated against this suite before being merged.**

Re-run after pricing changes and compare output to the baseline in `docs/pricing-validation/reports/`.

## Purpose

The validation suite answers four questions for every supported application archetype:

1. **Realism** — Do monthly Azure costs fall within engineering-judgment expected ranges?
2. **Consistency** — Are usage assumptions, free tier deductions, and component totals internally coherent?
3. **Completeness** — Are all billable SKUs priced, or are gaps explicitly reported?
4. **Pipeline quality** — Which pricing pipeline stage (assumptions, SKUs, catalog, etc.) needs improvement?

---

## Validation Methodology

Each run executes the full production pricing pipeline (stages 1–8):

| Stage | Description |
|-------|-------------|
| 1 | Architecture / component input |
| 2 | Usage assumptions (inferred) |
| 3 | Resolved assumptions |
| 4 | Raw SKU quantities |
| 5 | Free tier / included usage deducted |
| 6 | Billable SKU quantities |
| 7 | Catalog price lookup (`azure_catalog`) |
| 8 | Final SKU cost → component subtotal |

**Inference mode:** Heuristic fallback by default (`AzureUsageModelBuilder` + scale bands). LLM inference: `--inference llm`.

**Catalog:** Benchmark runs use `AzureCatalogTestFixture` (deterministic, CI-friendly). Production uses live synced Firestore `azure_catalog`.

### How to run

```bash
cd backend

# Full suite (44 runs: 11 scenarios x 4 user counts)
python scripts/run_azure_pricing_validation.py

# Single scenario
python scripts/run_azure_pricing_validation.py --scenario static_website

# JSON output
python scripts/run_azure_pricing_validation.py --json

pytest tests/test_azure_pricing_validation_suite.py
```

Reports are written to `docs/pricing-validation/reports/`:

| File | Contents |
|------|----------|
| `suite_summary_<timestamp>.txt` | Cost matrix, expected-range validation, suite status |
| `<scenario_id>_<users>_users.txt` | Full per-run pipeline trace |
| `assessments_<timestamp>.txt` | Category scores + human validation reviews |
| `suite_<timestamp>.json` | Machine-readable baseline for regression diff |

---

## Expected Cost Ranges

Ranges are defined in `backend/app/pricing/azure/expected_cost_ranges.py`. They encode Azure pricing guidance and engineering judgment — **not** exact calculator targets.

If actual cost falls outside the range, the run receives a **WARN** on the `expected_cost_range` rule. Update ranges deliberately when pricing behavior changes intentionally.

Example (from latest benchmark run):

```
Scenario                Users     Expected Range      Actual     Status
-----------------------------------------------------------------------
Simple CRUD SaaS        100       $30-$60             $37.69     OK
Self-Esteem / Habit     100K      $6,000-$10,000     $8,480     OK
AI Chat                 100K      $8,000-$15,000      $9,980     OK
Static Website          100       $2-$15              $4.06      OK
E-Commerce              100K      $18,000-$30,000     $24,584    OK
```

All 44 runs currently pass expected-range validation (2026-07-03).

---

## Pipeline Category Scores

Each scenario assessment includes scores from 1–10 for six categories (replacing a single overall confidence number):

| Category | What it measures |
|----------|------------------|
| **Usage Assumptions** | Per-user rate stability, inference quality |
| **Azure Service Selection** | Curated engineering review of architecture fit |
| **SKU Quantity Calculation** | Totals match components, no ignored SKUs, non-negative qty |
| **Free Tier / Included Usage** | Allowances and tier inclusions applied correctly |
| **Catalog Price Mapping** | All billable SKUs priced, no silent $0 |
| **Overall** | Weighted rollup across categories |

Typical scores on the current benchmark: **8–9/10 overall** for most scenarios. Lower **Azure Service Selection** (7/10) on Social Network and Static Website reflects known catalog gaps (no Cosmos DB, Static Web Apps, or CDN).

---

## Human Validation

Curated engineering reviews live in `backend/app/pricing/azure/human_validation.py`. These are **written judgment**, not generated from run output, and are updated when pricing behavior materially changes.

Each scenario assessment includes:

- Does this estimate look realistic? Why?
- Largest cost drivers
- Assumptions with greatest impact
- Assumptions that should probably be refined
- Review summary

See `assessments_<timestamp>.txt` in the reports folder for full text.

---

## Test Scenarios

All scenarios in `backend/app/pricing/azure/scenarios.py` run at **100**, **1,000**, **10,000**, and **100,000** users.

| # | Scenario ID | Architecture summary |
|---|-------------|---------------------|
| 1 | `simple_crud_saas` | Container Apps + SQL + Blob |
| 2 | `self_esteem_habit` | Container Apps + SQL + Blob + Queue |
| 3 | `ecommerce` | Container Apps + SQL + Blob + Service Bus + Functions |
| 4 | `ai_chat` | Container Apps + SQL + Blob + Functions |
| 5 | `ai_document_ocr` | Container Apps + Blob + Queue + Functions |
| 6 | `file_storage_drive` | Container Apps + SQL + Blob |
| 7 | `social_network` | Container Apps + SQL + Blob + Service Bus |
| 8 | `video_processing` | Container Apps + Blob + Queue + Functions |
| 9 | `background_job_platform` | Container Apps + Service Bus + Queue + Functions |
| 10 | `analytics_dashboard` | Container Apps + SQL + Blob |
| 11 | `static_website` | **Blob + Functions only (no database)** |

### 11. Static Website / Marketing Landing Page (`static_website`)

**Product:** Marketing landing page with static HTML/CSS/JS and a contact form. No user accounts or database.

**Expected architecture:** Azure Blob Storage + Azure Functions

**Why these services:** Blob hosts static assets (CDN/static-hosting pattern). Functions handles occasional form POSTs. **No SQL** — verifies the engine does not assume every app is CRUD SaaS.

**Expected behavior:** ~$4/mo at 100 users vs ~$38 for CRUD SaaS (no SQL S1 floor). Blob read/egress dominates at high traffic.

**Human validation highlight:** Real high-traffic sites would use Azure CDN / Front Door / Static Web Apps (not yet in catalog). Benchmark still validates the low-database-cost baseline correctly.

Detailed product descriptions for scenarios 1–10 are unchanged from the prior version; see git history or `scenarios.py` for full text.

---

## User Counts

| Label | `Project.expected_users` | Benchmark `users` |
|-------|--------------------------|-------------------|
| 100 | `"100"` | 100 |
| 1,000 | `"1000"` | 1,000 |
| 10,000 | `"10000"` | 10,000 |
| 100,000 | `"100000+"` | 100,000 |

---

## Validation Checklist

Each run automatically verifies:

| Rule | Description |
|------|-------------|
| **Expected cost range** | Actual total within engineering-judgment range (WARN if outside) |
| Cost monotonicity | Total does not decrease as users increase |
| Per-user behavior | Derived per-user rates stable across scales (+/-5%) |
| No silent zero | Billable usage never priced at $0 due to missing catalog |
| Free tier | Free tier deductions applied where configured |
| Included usage | Tier/plan inclusions applied where configured |
| Catalog prices | Every billable SKU resolves to a catalog unit price |
| Missing prices reported | Gaps surfaced in warnings / missing_prices |
| No negative quantities | Raw, billable, and deduction quantities >= 0 |
| Component cost reasonable | No single component exceeds 95% of total (WARN) |
| Total = components | Project total equals sum of component subtotals |

Status codes: **PASS**, **WARN**, **FAIL**.

---

## Current Findings

**Last run:** 2026-07-03 (heuristic inference, test catalog)

**Suite status:** 44 runs — **0 failures**, all expected ranges **OK**

### Cost summary (USD / month)

| Scenario | 100 | 1,000 | 10,000 | 100,000 |
|----------|-----|-------|--------|---------|
| Simple CRUD SaaS | $37.69 | $106.86 | $843.55 | $8,454.16 |
| Self-Esteem / Habit Tracking | $37.71 | $107.11 | $846.12 | $8,479.93 |
| E-Commerce | $52.18 | $256.20 | $2,464.79 | $24,583.79 |
| AI Chat | $39.21 | $122.09 | $995.83 | $9,979.72 |
| AI Document / OCR | $11.07 | $111.69 | $1,121.05 | $11,245.83 |
| File Storage / Drive | $40.66 | $230.97 | $2,302.51 | $23,046.37 |
| Social Network | $50.66 | $240.97 | $2,312.51 | $23,058.24 |
| Video Processing | $11.07 | $111.69 | $1,121.05 | $11,245.83 |
| Background Job Platform | $16.61 | $76.18 | $674.20 | $6,687.40 |
| Analytics Dashboard | $37.69 | $106.86 | $843.55 | $8,454.16 |
| **Static Website** | **$4.06** | **$40.61** | **$406.08** | **$4,063.56** |

### Category score summary (typical)

| Scenario | Usage | Service Sel. | SKU Qty | Free Tier | Catalog | Overall |
|----------|-------|--------------|---------|-----------|---------|---------|
| Simple CRUD SaaS | 8 | 9 | 10 | 9 | 10 | 9 |
| Static Website | 8 | 7 | 10 | 9 | 10 | 9 |
| AI Chat | 8 | 8 | 10 | 9 | 10 | 9 |
| Social Network | 8 | 7 | 10 | 9 | 10 | 9 |
| E-Commerce | 10 | 9 | 10 | 9 | 10 | 10 |

(Full scores in `assessments_*.txt`.)

---

## Strengths of the Pricing Engine

- **End-to-end traceability** — Every component cost decomposes through stages 1–8 with SKU-level audit.
- **Free tier and included usage** — Project-level pool sharing and tier deductions are applied before billing.
- **Monotonic scaling** — All 11 scenarios show increasing totals from 100 to 100k users.
- **Architecture diversity** — Static website (no SQL) validates non-CRUD patterns; async scenarios exercise Queue + Functions.
- **Explicit gap reporting** — Missing catalog prices and unpriced billable usage surface as warnings, not silent $0.
- **Regression-ready** — JSON suite output supports diff-based CI gates.

---

## Known Limitations

- **Heuristic inference default** — Usage assumptions come from scale bands, not LLM behavioral models. Per-user rate drift warnings are expected.
- **Fixed SQL tier** — Standard S1 (~$30/mo) applies at all scales; no automatic tier escalation.
- **External services excluded** — OpenAI/Anthropic API costs, Azure AI Document Intelligence, CDN/Front Door, Static Web Apps not in catalog.
- **Test catalog vs production** — Benchmark uses simplified Firestore fixture; live catalog may have different meter coverage.
- **Video/OCR compute** — Functions defaults understate long-running transcode/OCR duration.
- **Social graph on SQL** — Social Network scenario uses SQL for convenience; Cosmos DB would be more realistic at 100k users.

---

## Remaining Assumptions

- Sessions/month and requests/session derived from generic `AzureUsageModelBuilder` defaults
- `ai=True` and `file_upload=True` apply multipliers without product-specific profiles
- SQL storage grows linearly with users; no archival or tiering
- Container Apps min/max replicas use heuristic defaults, not workload profiling
- Blob read operations proxy page views for static sites (no CDN cache hit ratio)
- Functions execution duration uses model defaults, not per-workload benchmarks

---

## Recommended Future Improvements

1. **CI regression gate** — Run `run_azure_pricing_validation.py` on every PR touching `backend/app/pricing/`; fail on new FAIL statuses or unexpected range violations.
2. **Baseline JSON snapshots** — Commit golden `suite_baseline.json`; diff totals and category scores in CI.
3. **LLM inference track** — Parallel benchmark with `--inference llm`; compare to heuristic baseline.
4. **Live catalog mode** — `--catalog live` flag for pre-release validation against synced Firestore.
5. **SQL tier escalation** — Model DTU/vCore upgrades at 10k+ users.
6. **Static Web Apps / CDN catalog** — Add meters for Static Website scenario high-traffic path.
7. **External AI passthrough** — Separate cost line for third-party LLM APIs in AI scenarios.
8. **Product-specific profiles** — Per-scenario overrides in `AzureUsageModelBuilder`.

---

## Validation Coverage

| Area | Covered | Notes |
|------|---------|-------|
| Azure Container Apps | Yes | 10/11 scenarios |
| Azure SQL Database | Yes | 8/11 scenarios (excludes OCR, video, jobs, static) |
| Azure Blob Storage | Yes | All scenarios |
| Azure Queue Storage | Yes | 5 scenarios |
| Azure Service Bus | Yes | 3 scenarios |
| Azure Functions | Yes | 6 scenarios |
| Expected cost ranges | Yes | All 44 runs |
| Human engineering review | Yes | All 11 scenarios |
| Pipeline category scores | Yes | All 11 scenarios |
| LLM inference path | Partial | Manual via `--inference llm` |
| Live Firestore catalog | No | Test fixture only |
| AWS / GCP pricing | No | Azure-only suite |

---

## Regression Checklist

Before merging any pricing change:

- [ ] Run `python scripts/run_azure_pricing_validation.py` from `backend/`
- [ ] Confirm **0 FAIL** statuses in suite summary
- [ ] Review any new **WARN** on expected cost ranges — update ranges if change is intentional
- [ ] Compare `suite_<timestamp>.json` totals to last baseline (cost matrix should not drop unexpectedly)
- [ ] Run `pytest tests/test_azure_pricing_validation_suite.py tests/test_benchmark_azure_component_pricing.py`
- [ ] If usage inference changed, spot-check `assessments_*.txt` human validation still applies
- [ ] If catalog meters added/changed, verify **Catalog Price Mapping** scores remain >= 8
- [ ] Update `expected_cost_ranges.py` if new behavior is correct but outside old ranges
- [ ] Update `human_validation.py` if architecture or dominant cost drivers materially changed
- [ ] Update this document's **Current Findings** section with new run date and summary table

---

## Code Map

| File | Role |
|------|------|
| `backend/app/pricing/azure/scenarios.py` | Scenario definitions (11 archetypes) |
| `backend/app/pricing/azure/expected_cost_ranges.py` | Engineering-judgment cost ranges |
| `backend/app/pricing/azure/human_validation.py` | Curated engineering reviews |
| `backend/app/pricing/azure/validation_suite.py` | Rules, reports, category scores |
| `backend/app/pricing/azure/benchmark.py` | Legacy table benchmark (self-esteem) |
| `backend/app/pricing/azure/verification.py` | Pipeline runner (stages 1–8) |
| `backend/scripts/run_azure_pricing_validation.py` | CLI entry point |
| `backend/tests/test_azure_pricing_validation_suite.py` | Automated tests |
| `docs/pricing-validation/reports/` | Generated benchmark output |

---

## Per-Run Report Structure

Each `<scenario>_<users>_users.txt` report contains:

```
Scenario / Users / Architecture
Usage Assumptions (per-user behavior, inferred, confidence, reasoning)
Component Breakdown (per Azure service)
  - Raw SKU quantities
  - Free tier deduction
  - Included usage deduction
  - Billable quantities
  - Unit prices
  - Monthly component cost
Project Summary
  - Total monthly Azure cost
  - Expected cost range vs actual
  - Cost per user
  - Largest cost drivers
  - Warnings / missing prices / pricing completeness
Validation Checks (PASS / WARN / FAIL)
```

Use these reports as the authoritative reference when investigating pricing regressions.
