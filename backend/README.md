# Architecture Planner — Backend

## Cost Calculation Architecture

```
Users + Architecture + Capabilities + Stage
        ↓
   Usage Estimator          (provider-independent resource consumption)
        ↓
   Component Allocator      (per-component resource slices)
        ↓
   Pricing Engine           (Firestore SKUs → monthly cost)
        ↓
   Cost Aggregator          (sum per provider, apply ranges)
```

### 1. Usage Estimator (`app/services/usage_estimation/`)

Estimates **resource consumption only** — no AWS/GCP/Azure pricing knowledge.

**Inputs:** expected users, architecture components, product capabilities (auth, uploads, AI, etc.), stage.

**Outputs:** `ResourceConsumption` with normalized metrics:

- `monthly_requests`, `cpu_seconds`, `memory_gib_seconds`
- `storage_gb`, `outbound_network_gb`
- `database_reads`, `database_writes`, `database_storage_gb`
- `queue_messages`, `cache_memory_gb`
- `input_tokens`, `output_tokens`, `ai_requests`
- `emails_sent`, `push_notifications`, `sms_messages`
- `log_gb`, `metric_samples`, `instance_hours`, `instances`

Assumptions are tuned via `USAGE_ESTIMATION_BASE` and `USAGE_CAPABILITY_MULTIPLIERS` in `params.py`.

### 2. Component Usage Allocator

Maps global consumption to **per-component slices** so each billable component only receives relevant metrics (e.g. storage components get `storage_gb`, not full API request volume).

### 3. Pricing Engine (`app/services/cost_calculation/pricing_engine.py`)

Receives normalized usage metrics and applies Firestore catalog SKUs + formulas via model-specific calculators.

| Model | Metrics used |
|-------|----------------|
| `compute_request_based` | `cpu_seconds`, `memory_gib_seconds`, `monthly_requests` |
| `database_request_based` | `database_reads`, `database_writes`, `database_storage_gb` |
| `storage_based` | `storage_gb`, `outbound_network_gb` |
| `token_based` | `input_tokens`, `output_tokens` |

### 4. Cost Aggregator (`architecture_cost_calculator.py`)

Sums component costs per provider, splits required/optional, applies low/high range factors (0.75× / 1.35×), and attaches audit breakdowns.

### Audit breakdown

Each component in `component_breakdown` includes usage assumptions, SKU line items, validation warnings, and final cost — see `tests/test_cost_audit_breakdown.py`.

### Key files

| Layer | Path |
|-------|------|
| Usage estimation | `app/services/usage_estimation/` |
| Pricing | `app/services/cost_calculation/pricing_engine.py`, `calculators/` |
| Aggregation | `app/services/cost_calculation/architecture_cost_calculator.py` |
| Config | `app/config/params.py` (`USAGE_ESTIMATION_BASE`) |
| Tests | `tests/test_usage_estimator.py`, `tests/test_cost_audit_breakdown.py` |
