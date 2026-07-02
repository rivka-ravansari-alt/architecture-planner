# Pricing Audit Report

Read-only audit of the current SKU-based pricing pipeline. No pricing logic was modified.

---

## Scenario: TaskFlow

_Small team task manager, MVP, ~100 users_

- Users: **100** | Stage: **mvp**
- Requirements: `{'auth': True, 'file_upload': True, 'background_processing': False, 'ai': False, 'dashboards': False, 'payments': False}`

### Component: Web Client (`web_app`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Amplify Hosting | $0.03–$0.04 | medium |
| GCP | Firebase Hosting | $0.00–$0.00 | low |
| AZURE | Azure App Service | $12.75–$17.25 | medium |

- Nominal (low) cost spread across providers: $12.75/month (gcp=$0.00 vs azure=$12.75).
- Mapped equivalents: AWS=Amplify Hosting, GCP=Firebase Hosting, AZURE=Azure App Service. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs

#### AWS — Amplify Hosting

**Monthly estimate:** $0.03 – $0.04

**Service selection**
- Architecture options: `['Amplify Hosting']`
- Selected: **Amplify Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 25 | — | $0.00 |
| requests | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 600 | — | $0.03 |

**SKU selection notes**

- Selected hosting storage SKU: requests.
- Selected hosting requests SKU: requests.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 45
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 120
  - `memory`: 0.0125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 120
  - `monthly_gb_seconds`: 45
  - `monthly_memory_gib_hours`: 0.0125
  - `monthly_requests`: 600
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0063
  - `requests`: 600
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0063

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.03
  Storage Cost           $      0.00
  Total                  $      0.03  (range $0.03–$0.04)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: requests.; Selected hosting requests SKU: requests.

#### GCP — Firebase Hosting

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Firebase Hosting']`
- Selected: **Firebase Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No priced hosting storage SKU found in catalog.
- No priced hosting requests SKU found in catalog.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 45
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 120
  - `memory`: 0.0125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 120
  - `monthly_gb_seconds`: 45
  - `monthly_memory_gib_hours`: 0.0125
  - `monthly_requests`: 600
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0063
  - `requests`: 600
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0063

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced hosting storage SKU found in catalog.; No priced hosting requests SKU found in catalog.; no_priced_skus:web_app
- Fuzzy / fallback matching:
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.

#### AZURE — Azure App Service

**Monthly estimate:** $12.75 – $17.25

**Service selection**
- Architecture options: `['Azure App Service']`
- Selected: **Azure App Service**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 25 | — | $0.51 |
| requests | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 600 | — | $14.40 |

**SKU selection notes**

- Selected hosting storage SKU: standard.
- Selected hosting requests SKU: standard.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 45
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 120
  - `memory`: 0.0125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 120
  - `monthly_gb_seconds`: 45
  - `monthly_memory_gib_hours`: 0.0125
  - `monthly_requests`: 600
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0063
  - `requests`: 600
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0063

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $     14.40
  Storage Cost           $      0.60
  Total                  $     12.75  (range $12.75–$17.25)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: standard.; Selected hosting requests SKU: standard.

---

### Component: API Gateway (`api_gateway`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | API Gateway | $0.00–$0.00 | medium |
| GCP | API Gateway | $0.00–$0.00 | low |
| AZURE | API Management | $0.00–$0.00 | low |

- Nominal (low) cost spread across providers: $0.00/month (aws=$0.00 vs aws=$0.00).
- Mapped equivalents: AWS=API Gateway, GCP=API Gateway, AZURE=API Management. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: unusually high requests cost ($4200) — verify SKU/unit
  - AZURE: fallback or weak catalog match
  - AZURE: unusually high requests cost ($4200) — verify SKU/unit

#### AWS — API Gateway

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | FC2TWT2UEPTBKVBX | $1/million requests - API Gateway HTTP API (first 300 millio | $0.00000100 | Requests | 1400 | — | $0.00 |

**SKU selection notes**

- Selected API calls SKU: requests.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 105
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 280
  - `memory`: 0.0292
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 280
  - `monthly_gb_seconds`: 105
  - `monthly_memory_gib_hours`: 0.0292
  - `monthly_requests`: 1400
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0146
  - `requests`: 1400
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0146

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected API calls SKU: requests.

#### GCP — API Gateway

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 1400 | — | $4200.00 |

**SKU selection notes**

- No priced API calls SKU found in catalog.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 105
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 280
  - `memory`: 0.0292
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 280
  - `monthly_gb_seconds`: 105
  - `monthly_memory_gib_hours`: 0.0292
  - `monthly_requests`: 1400
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0146
  - `requests`: 1400
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0146

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- Computed monthly cost is zero.
- Fallback pricing was used because the catalog lacked a suitable SKU.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced API calls SKU found in catalog.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.

#### AZURE — API Management

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Management']`
- Selected: **API Management**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 1400 | — | $4200.00 |

**SKU selection notes**

- Selected API calls SKU: gateway.
- Ignored capacity/egress SKUs for API call pricing.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 105
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 280
  - `memory`: 0.0292
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 280
  - `monthly_gb_seconds`: 105
  - `monthly_memory_gib_hours`: 0.0292
  - `monthly_requests`: 1400
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0146
  - `requests`: 1400
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0146

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- Computed monthly cost is zero.
- Fallback pricing was used because the catalog lacked a suitable SKU.
- Selection / default notes: Selected API calls SKU: gateway.; Ignored capacity/egress SKUs for API call pricing.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - Ignored capacity/egress SKUs for API call pricing.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - Ignored capacity/egress SKUs for API call pricing.
  - No API call SKU in catalog; using fallback $3.00/million requests.

---

### Component: Backend API (`app_service`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Lambda | $0.00–$0.00 | medium |
| GCP | Cloud Run | $0.00–$0.00 | medium |
| AZURE | Functions | $0.00–$0.00 | medium |

- Nominal (low) cost spread across providers: $0.00/month (aws=$0.00 vs aws=$0.00).
- Mapped equivalents: AWS=Lambda, GCP=Cloud Run, AZURE=Functions. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Lambda

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Lambda']`
- Selected: **Lambda**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 1200 | — | $0.00 |
| execution | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 240 | — | $0.00 |

**SKU selection notes**

- Selected requests SKU: requests.
- Selected gb-seconds SKU: requests.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 90
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 240
  - `memory`: 0.025
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 240
  - `monthly_gb_seconds`: 90
  - `monthly_memory_gib_hours`: 0.025
  - `monthly_requests`: 1200
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0125
  - `requests`: 1200
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0125

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Duration Cost          $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected requests SKU: requests.; Selected gb-seconds SKU: requests.

#### GCP — Cloud Run

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.25 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 0.025 | — | $0.00 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 1200 | — | $0.00 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 90
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 240
  - `memory`: 0.025
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 240
  - `monthly_gb_seconds`: 90
  - `monthly_memory_gib_hours`: 0.025
  - `monthly_requests`: 1200
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0125
  - `requests`: 1200
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0125

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.00
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Functions

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Functions']`
- Selected: **Functions**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| execution | DZH318Z0DW2R/00BL | Always Ready Baseline | $0.00000500 | 1 GB Second | 240 | — | $0.00 |
| cpu | DZH318Z0BXVK/000L | Premium vCPU Duration | $0.17500000 | 1 Hour | 0.25 | — | $0.04 |
| memory | DZH318Z0BXVK/000J | Premium Memory Duration | $0.01300000 | 1 GiB Hour | 0.025 | — | $0.00 |

**SKU selection notes**

- Selected execution SKU: always_ready.
- Selected cpu SKU: cpu.
- Selected memory SKU: memory.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 90
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 240
  - `memory`: 0.025
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 240
  - `monthly_gb_seconds`: 90
  - `monthly_memory_gib_hours`: 0.025
  - `monthly_requests`: 1200
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0125
  - `requests`: 1200
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0125

**Formula**

```
  Execution Cost = monthly_executions * skus.execution.unit_price_usd
  Vcpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Total = execution_cost + vcpu_cost + memory_cost
```

**Cost contribution**

```
  Execution Cost         $      0.00
  Vcpu Cost              $      0.00
  Memory Cost            $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected execution SKU: always_ready.; Selected cpu SKU: cpu.; Selected memory SKU: memory.

---

### Component: Authentication (`auth`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Cognito | $0.00–$0.00 | low |
| GCP | Firebase Authentication | $0.00–$0.00 | low |
| AZURE | Entra ID B2C | $0.00–$0.00 | low |

- Nominal (low) cost spread across providers: $0.00/month (aws=$0.00 vs aws=$0.00).
- Mapped equivalents: AWS=Cognito, GCP=Firebase Authentication, AZURE=Entra ID B2C. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - AWS: $0 — likely missing catalog or SKUs
  - GCP: $0 — likely missing catalog or SKUs
  - AZURE: $0 — likely missing catalog or SKUs

#### AWS — Cognito

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cognito']`
- Selected: **Cognito**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 30
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 80
  - `memory`: 0.0083
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 80
  - `monthly_gb_seconds`: 30
  - `monthly_memory_gib_hours`: 0.0083
  - `monthly_requests`: 400
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0042
  - `requests`: 400
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0042

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:aws:Cognito

#### GCP — Firebase Authentication

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Firebase Authentication']`
- Selected: **Firebase Authentication**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 30
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 80
  - `memory`: 0.0083
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 80
  - `monthly_gb_seconds`: 30
  - `monthly_memory_gib_hours`: 0.0083
  - `monthly_requests`: 400
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0042
  - `requests`: 400
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0042

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:gcp:Firebase Authentication

#### AZURE — Entra ID B2C

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Entra ID B2C']`
- Selected: **Entra ID B2C**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 30
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 80
  - `memory`: 0.0083
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 80
  - `monthly_gb_seconds`: 30
  - `monthly_memory_gib_hours`: 0.0083
  - `monthly_requests`: 400
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0042
  - `requests`: 400
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0042

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:azure:Entra ID B2C

---

### Component: Database (`database`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | DynamoDB | $2.13–$2.88 | medium |
| GCP | Cloud Firestore | $0.00–$0.00 | low |
| AZURE | Azure Cosmos DB | $1.06–$1.44 | medium |

- Nominal (low) cost spread across providers: $2.13/month (gcp=$0.00 vs aws=$2.13).
- Mapped equivalents: AWS=DynamoDB, GCP=Cloud Firestore, AZURE=Azure Cosmos DB. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs

#### AWS — DynamoDB

**Monthly estimate:** $2.13 – $2.88

**Service selection**
- Architecture options: `['DynamoDB']`
- Selected: **DynamoDB**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | 4W4ZMC46EHE8XTTZ | $0.125 per million read request units (N. Virginia) | $0.00000012 | ReadRequestUnits | 200 | — | $0.00 |
| storage | 3ADXMU9RYGKRUA9W | $0.10000 per GB of data exported in US East (N. Virginia) | $0.10000000 | GB | 25 | — | $2.12 |

**SKU selection notes**

- Selected read/write requests SKU: requests.
- Selected storage SKU: use1_exportdatasize_bytes.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 15
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 40
  - `memory`: 0.0042
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 40
  - `monthly_gb_seconds`: 15
  - `monthly_memory_gib_hours`: 0.0042
  - `monthly_requests`: 200
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0021
  - `requests`: 200
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0021

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $      2.50
  Total                  $      2.13  (range $2.13–$2.88)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected read/write requests SKU: requests.; Selected storage SKU: use1_exportdatasize_bytes.

#### GCP — Cloud Firestore

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Firestore']`
- Selected: **Cloud Firestore**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No read/write requests SKU found in catalog.
- No priced storage SKU found in catalog.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 15
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 40
  - `memory`: 0.0042
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 40
  - `monthly_gb_seconds`: 15
  - `monthly_memory_gib_hours`: 0.0042
  - `monthly_requests`: 200
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0021
  - `requests`: 200
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0021

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No read/write requests SKU found in catalog.; No priced storage SKU found in catalog.; no_priced_skus:database
- Fuzzy / fallback matching:
  - No priced storage SKU found in catalog.
  - No priced storage SKU found in catalog.

#### AZURE — Azure Cosmos DB

**Monthly estimate:** $1.06 – $1.44

**Service selection**
- Architecture options: `['Azure Cosmos DB']`
- Selected: **Azure Cosmos DB**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | DZH318Z0CDGF/0019 | Standard Read Operations | $0.00400000 | 10K | 200 | — | $0.80 |
| storage | DZH318Z0CF60/0005 | 256 GiB Disk | $0.05000000 | 1/Hour | 25 | — | $1.06 |

**SKU selection notes**

- Selected read/write requests SKU: standard.
- Selected storage SKU: memory.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 15
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 40
  - `memory`: 0.0042
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 40
  - `monthly_gb_seconds`: 15
  - `monthly_memory_gib_hours`: 0.0042
  - `monthly_requests`: 200
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0021
  - `requests`: 200
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0021

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $      1.25
  Total                  $      1.06  (range $1.06–$1.44)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected read/write requests SKU: standard.; Selected storage SKU: memory.

---

### Component: File Storage (`object_storage`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | S3 | $2.05–$2.78 | medium |
| GCP | Cloud Storage | $0.85–$1.15 | medium |
| AZURE | Blob Storage | $1.32–$1.78 | medium |

- Nominal (low) cost spread across providers: $1.20/month (gcp=$0.85 vs aws=$2.05).
- Mapped equivalents: AWS=S3, GCP=Cloud Storage, AZURE=Blob Storage. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — S3

**Monthly estimate:** $2.05 – $2.78

**Service selection**
- Architecture options: `['S3']`
- Selected: **S3**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 25 | — | $0.49 |
| requests | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 80 | — | $1.84 |

**SKU selection notes**

- Selected object storage SKU: earlydelete_int.
- Selected storage operations SKU: earlydelete_int.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 6
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 16
  - `memory`: 0.0017
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 16
  - `monthly_gb_seconds`: 6
  - `monthly_memory_gib_hours`: 0.0017
  - `monthly_requests`: 80
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0008
  - `requests`: 80
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0008

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      1.84
  Storage Cost           $      0.57
  Total                  $      2.05  (range $2.05–$2.78)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: earlydelete_int.; Selected storage operations SKU: earlydelete_int.

#### GCP — Cloud Storage

**Monthly estimate:** $0.85 – $1.15

**Service selection**
- Architecture options: `['Cloud Storage']`
- Selected: **Cloud Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | 0A5B-5BB2-9A38 | Cloud CDN Cache Fill from Europe to Middle East | $0.04000000 | GiBy | 25 | — | $0.85 |
| requests | 007A-40B7-63BC | Multi-Region Durable Reduced Availability Class A Operations | $0.00002000 | count | 80 | — | $0.00 |

**SKU selection notes**

- Selected object storage SKU: cdncachefill_ondemand.
- Selected storage operations SKU: draops_ondemand.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 6
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 16
  - `memory`: 0.0017
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 16
  - `monthly_gb_seconds`: 6
  - `monthly_memory_gib_hours`: 0.0017
  - `monthly_requests`: 80
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0008
  - `requests`: 80
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0008

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $      1.00
  Total                  $      0.85  (range $0.85–$1.15)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: cdncachefill_ondemand.; Selected storage operations SKU: draops_ondemand.

#### AZURE — Blob Storage

**Monthly estimate:** $1.32 – $1.78

**Service selection**
- Architecture options: `['Blob Storage']`
- Selected: **Blob Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z0BNWT/00CD | ZRS Data Stored | $0.06190000 | 1 GB/Month | 25 | — | $1.32 |
| requests | DZH318Z0CBTJ/05R9 | Smart Tier GRS Monitoring Operations | $0.04000000 | 10K | 80 | — | $3.20 |

**SKU selection notes**

- Selected object storage SKU: storage.
- Selected storage operations SKU: smart_tier_grs.

**Usage assumptions**

- expected_users: 100
- user_count: 100
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 6
  - `egress`: 2.4
  - `egress_gb`: 2.4
  - `execution`: 16
  - `memory`: 0.0017
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 800
  - `monthly_executions`: 16
  - `monthly_gb_seconds`: 6
  - `monthly_memory_gib_hours`: 0.0017
  - `monthly_requests`: 80
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0008
  - `requests`: 80
  - `storage`: 25
  - `storage_gib`: 25
  - `vcpu`: 0.0008

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $      1.55
  Total                  $      1.32  (range $1.32–$1.78)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: storage.; Selected storage operations SKU: smart_tier_grs.

---

## Scenario: ShopLite

_E-commerce storefront, MVP, ~1,000 users, uploads + payments_

- Users: **1000** | Stage: **mvp**
- Requirements: `{'auth': True, 'file_upload': True, 'background_processing': False, 'ai': False, 'dashboards': False, 'payments': True}`

### Component: Storefront (`web_app`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Amplify Hosting | $0.30–$0.40 | medium |
| GCP | Firebase Hosting | $0.00–$0.00 | low |
| AZURE | Azure App Service | $127.50–$172.50 | medium |

- Nominal (low) cost spread across providers: $127.50/month (gcp=$0.00 vs azure=$127.50).
- Mapped equivalents: AWS=Amplify Hosting, GCP=Firebase Hosting, AZURE=Azure App Service. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs

#### AWS — Amplify Hosting

**Monthly estimate:** $0.30 – $0.40

**Service selection**
- Architecture options: `['Amplify Hosting']`
- Selected: **Amplify Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 250 | — | $0.01 |
| requests | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 6000 | — | $0.33 |

**SKU selection notes**

- Selected hosting storage SKU: requests.
- Selected hosting requests SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 450
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 1200
  - `memory`: 0.125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 1200
  - `monthly_gb_seconds`: 450
  - `monthly_memory_gib_hours`: 0.125
  - `monthly_requests`: 6000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0625
  - `requests`: 6000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0625

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.33
  Storage Cost           $      0.01
  Total                  $      0.30  (range $0.30–$0.40)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: requests.; Selected hosting requests SKU: requests.

#### GCP — Firebase Hosting

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Firebase Hosting']`
- Selected: **Firebase Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No priced hosting storage SKU found in catalog.
- No priced hosting requests SKU found in catalog.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 450
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 1200
  - `memory`: 0.125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 1200
  - `monthly_gb_seconds`: 450
  - `monthly_memory_gib_hours`: 0.125
  - `monthly_requests`: 6000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0625
  - `requests`: 6000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0625

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced hosting storage SKU found in catalog.; No priced hosting requests SKU found in catalog.; no_priced_skus:web_app
- Fuzzy / fallback matching:
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.

#### AZURE — Azure App Service

**Monthly estimate:** $127.50 – $172.50

**Service selection**
- Architecture options: `['Azure App Service']`
- Selected: **Azure App Service**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 250 | — | $5.10 |
| requests | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 6000 | — | $144.00 |

**SKU selection notes**

- Selected hosting storage SKU: standard.
- Selected hosting requests SKU: standard.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 450
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 1200
  - `memory`: 0.125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 1200
  - `monthly_gb_seconds`: 450
  - `monthly_memory_gib_hours`: 0.125
  - `monthly_requests`: 6000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0625
  - `requests`: 6000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0625

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $    144.00
  Storage Cost           $      6.00
  Total                  $    127.50  (range $127.50–$172.50)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: standard.; Selected hosting requests SKU: standard.

---

### Component: CDN (`cdn`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | CloudFront | $0.00–$0.00 | medium |
| GCP | Networking | $36.00–$36.00 | medium |
| AZURE | Content Delivery Network | $129.30–$129.30 | medium |

- Nominal (low) cost spread across providers: $129.30/month (aws=$0.00 vs azure=$129.30).
- Mapped equivalents: AWS=CloudFront, GCP=Networking, AZURE=Content Delivery Network. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — CloudFront

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['CloudFront']`
- Selected: **CloudFront**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | UH5MRG7QT9XX6YBP | $6.0E-7  per Request for  in US East (N. Virginia) | $0.00000060 | Request | 24 | — | $0.00 |

**SKU selection notes**

- Selected CDN egress SKU: requests.
- CDN egress assumed 300.0 GiB/month for 1000 users.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.2
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 600
  - `egress`: 24
  - `egress_gb`: 300
  - `execution`: 1600
  - `memory`: 0.1667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 1600
  - `monthly_gb_seconds`: 600
  - `monthly_memory_gib_hours`: 0.1667
  - `monthly_requests`: 8000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0833
  - `requests`: 8000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0833

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected CDN egress SKU: requests.; CDN egress assumed 300.0 GiB/month for 1000 users.

#### GCP — Networking

**Monthly estimate:** $36.00 – $36.00

**Service selection**
- Architecture options: `['Networking']`
- Selected: **Networking**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | 307A-FED8-5B99 | Networking Data Transfer inter region Intercontinental (Excl | $0.12000000 | GiBy | 24 | — | $36.00 |

**SKU selection notes**

- Selected CDN egress SKU: datatransfer_ondemand.
- CDN egress assumed 300.0 GiB/month for 1000 users.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.2
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 600
  - `egress`: 24
  - `egress_gb`: 300
  - `execution`: 1600
  - `memory`: 0.1667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 1600
  - `monthly_gb_seconds`: 600
  - `monthly_memory_gib_hours`: 0.1667
  - `monthly_requests`: 8000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0833
  - `requests`: 8000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0833

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $     36.00
  Total                  $     36.00  (range $36.00–$36.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: datatransfer_ondemand.; CDN egress assumed 300.0 GiB/month for 1000 users.

#### AZURE — Content Delivery Network

**Monthly estimate:** $129.30 – $129.30

**Service selection**
- Architecture options: `['Content Delivery Network']`
- Selected: **Content Delivery Network**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | DZH318Z0BXV8/000V | Custom Acceleration 2 Data Transfer | $0.43100000 | 1 GB | 24 | — | $129.30 |

**SKU selection notes**

- Selected CDN egress SKU: egress.
- CDN egress assumed 300.0 GiB/month for 1000 users.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.2
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 600
  - `egress`: 24
  - `egress_gb`: 300
  - `execution`: 1600
  - `memory`: 0.1667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 1600
  - `monthly_gb_seconds`: 600
  - `monthly_memory_gib_hours`: 0.1667
  - `monthly_requests`: 8000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0833
  - `requests`: 8000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0833

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $    129.30
  Total                  $    129.30  (range $129.30–$129.30)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: egress.; CDN egress assumed 300.0 GiB/month for 1000 users.

---

### Component: API Gateway (`api_gateway`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | API Gateway | $0.00–$0.00 | medium |
| GCP | API Gateway | $0.04–$0.05 | low |
| AZURE | API Management | $0.04–$0.05 | low |

- Nominal (low) cost spread across providers: $0.04/month (aws=$0.00 vs gcp=$0.04).
- Mapped equivalents: AWS=API Gateway, GCP=API Gateway, AZURE=API Management. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: unusually high requests cost ($42000) — verify SKU/unit
  - AZURE: fallback or weak catalog match
  - AZURE: unusually high requests cost ($42000) — verify SKU/unit

#### AWS — API Gateway

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | FC2TWT2UEPTBKVBX | $1/million requests - API Gateway HTTP API (first 300 millio | $0.00000100 | Requests | 14000 | — | $0.01 |

**SKU selection notes**

- Selected API calls SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1050
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 2800
  - `memory`: 0.2917
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 2800
  - `monthly_gb_seconds`: 1050
  - `monthly_memory_gib_hours`: 0.2917
  - `monthly_requests`: 14000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.1458
  - `requests`: 14000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.1458

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected API calls SKU: requests.

#### GCP — API Gateway

**Monthly estimate:** $0.04 – $0.05

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 14000 | — | $42000.00 |

**SKU selection notes**

- No priced API calls SKU found in catalog.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1050
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 2800
  - `memory`: 0.2917
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 2800
  - `monthly_gb_seconds`: 1050
  - `monthly_memory_gib_hours`: 0.2917
  - `monthly_requests`: 14000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.1458
  - `requests`: 14000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.1458

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.04
  Total                  $      0.04  (range $0.04–$0.05)
```

**Confidence: LOW**

- Fallback pricing was used because the catalog lacked a suitable SKU.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced API calls SKU found in catalog.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.

#### AZURE — API Management

**Monthly estimate:** $0.04 – $0.05

**Service selection**
- Architecture options: `['API Management']`
- Selected: **API Management**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 14000 | — | $42000.00 |

**SKU selection notes**

- Selected API calls SKU: gateway.
- Ignored capacity/egress SKUs for API call pricing.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1050
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 2800
  - `memory`: 0.2917
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 2800
  - `monthly_gb_seconds`: 1050
  - `monthly_memory_gib_hours`: 0.2917
  - `monthly_requests`: 14000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.1458
  - `requests`: 14000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.1458

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.04
  Total                  $      0.04  (range $0.04–$0.05)
```

**Confidence: LOW**

- Fallback pricing was used because the catalog lacked a suitable SKU.
- Selection / default notes: Selected API calls SKU: gateway.; Ignored capacity/egress SKUs for API call pricing.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - Ignored capacity/egress SKUs for API call pricing.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - Ignored capacity/egress SKUs for API call pricing.
  - No API call SKU in catalog; using fallback $3.00/million requests.

---

### Component: Order Service (`app_service`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Lambda | $0.00–$0.00 | medium |
| GCP | Cloud Run | $0.00–$0.01 | medium |
| AZURE | Functions | $0.03–$0.04 | medium |

- Nominal (low) cost spread across providers: $0.03/month (aws=$0.00 vs azure=$0.03).
- Mapped equivalents: AWS=Lambda, GCP=Cloud Run, AZURE=Functions. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Lambda

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Lambda']`
- Selected: **Lambda**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 12000 | — | $0.00 |
| execution | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 2400 | — | $0.00 |

**SKU selection notes**

- Selected requests SKU: requests.
- Selected gb-seconds SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 2400
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 2400
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.125

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Duration Cost          $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected requests SKU: requests.; Selected gb-seconds SKU: requests.

#### GCP — Cloud Run

**Monthly estimate:** $0.00 – $0.01

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.25 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 0.25 | — | $0.00 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 12000 | — | $0.00 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 2400
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 2400
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.125

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.01
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.01)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Functions

**Monthly estimate:** $0.03 – $0.04

**Service selection**
- Architecture options: `['Functions']`
- Selected: **Functions**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| execution | DZH318Z0DW2R/00BL | Always Ready Baseline | $0.00000500 | 1 GB Second | 2400 | — | $0.01 |
| cpu | DZH318Z0BXVK/000L | Premium vCPU Duration | $0.17500000 | 1 Hour | 0.25 | — | $0.04 |
| memory | DZH318Z0BXVK/000J | Premium Memory Duration | $0.01300000 | 1 GiB Hour | 0.25 | — | $0.00 |

**SKU selection notes**

- Selected execution SKU: always_ready.
- Selected cpu SKU: cpu.
- Selected memory SKU: memory.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 2400
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 2400
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.125

**Formula**

```
  Execution Cost = monthly_executions * skus.execution.unit_price_usd
  Vcpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Total = execution_cost + vcpu_cost + memory_cost
```

**Cost contribution**

```
  Execution Cost         $      0.01
  Vcpu Cost              $      0.02
  Memory Cost            $      0.00
  Total                  $      0.03  (range $0.03–$0.04)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected execution SKU: always_ready.; Selected cpu SKU: cpu.; Selected memory SKU: memory.

---

### Component: Product DB (`database`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | RDS | $79.12–$88.50 | medium |
| GCP | Cloud SQL | $33.63–$34.69 | medium |
| AZURE | SQL Database | $132.77–$175.61 | medium |

- Nominal (low) cost spread across providers: $99.14/month (gcp=$33.63 vs azure=$132.77).
- Mapped equivalents: AWS=RDS, GCP=Cloud SQL, AZURE=SQL Database. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — RDS

**Monthly estimate:** $79.12 – $88.50

**Service selection**
- Architecture options: `['RDS']`
- Selected: **RDS**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | KFZ3UNZPS5C5EB5P | USD 0.072 per db.t3.small Multi-AZ instance hour (or partial | $0.07200000 | Hrs | 730 | — | $52.56 |
| storage | 84K7WYHA9BB4ZQU3 | USD 0.125 per GB-Month of provisioned io2 storage for Single | $0.12500000 | GB-Mo | 250 | — | $26.56 |

**SKU selection notes**

- Selected instance tier SKU: multi_azusage_db_t3_small (target tier 3).
- Selected storage SKU: storage.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 400
  - `instance_billable_units`: 730
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 400
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = instance_cost + storage_cost
```

**Cost contribution**

```
  Instance Cost          $     52.56
  Storage Cost           $     31.25
  Total                  $     79.12  (range $79.12–$88.50)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected instance tier SKU: multi_azusage_db_t3_small (target tier 3).; Selected storage SKU: storage.

#### GCP — Cloud SQL

**Monthly estimate:** $33.63 – $34.69

**Service selection**
- Architecture options: `['Cloud SQL']`
- Selected: **Cloud SQL**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | 00FF-CE73-9FEC | Cloud SQL for PostgreSQL: Regional - Extended support f1-mic | $0.04200000 | h | 730 | — | $30.66 |
| storage | 0023-A861-3E87 | Cloud SQL for MySQL: Regional - RAM in Phoenix | $0.01400000 | GiBy.h | 250 | — | $2.98 |

**SKU selection notes**

- Selected instance tier SKU: sqlgen2instancesf1micro_ondemand (target tier 3).
- Selected storage SKU: memory.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 400
  - `instance_billable_units`: 730
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 400
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = instance_cost + storage_cost
```

**Cost contribution**

```
  Instance Cost          $     30.66
  Storage Cost           $      3.50
  Total                  $     33.63  (range $33.63–$34.69)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected instance tier SKU: sqlgen2instancesf1micro_ondemand (target tier 3).; Selected storage SKU: memory.

#### AZURE — SQL Database

**Monthly estimate:** $132.77 – $175.61

**Service selection**
- Architecture options: `['SQL Database']`
- Selected: **SQL Database**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | DZH318Z0BQHF/0065 | S0 Secondary DTUs | $0.37960000 | 1/Day | 1 | — | $11.39 |
| storage | DZH318Z0BQCL/002Z | Data Stored | $0.57120000 | 1 GB/Month | 250 | — | $121.38 |

**SKU selection notes**

- Selected instance tier SKU: s0_secondary (target tier 3).
- Selected storage SKU: storage.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 400
  - `instance_billable_units`: 30
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 400
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = instance_cost + storage_cost
```

**Cost contribution**

```
  Instance Cost          $     11.39
  Storage Cost           $    142.80
  Total                  $    132.77  (range $132.77–$175.61)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected instance tier SKU: s0_secondary (target tier 3).; Selected storage SKU: storage.

---

### Component: Product Images (`object_storage`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | S3 | $20.53–$27.77 | medium |
| GCP | Cloud Storage | $8.51–$11.52 | medium |
| AZURE | Blob Storage | $13.16–$17.80 | medium |

- Nominal (low) cost spread across providers: $12.02/month (gcp=$8.51 vs aws=$20.53).
- Mapped equivalents: AWS=S3, GCP=Cloud Storage, AZURE=Blob Storage. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — S3

**Monthly estimate:** $20.53 – $27.77

**Service selection**
- Architecture options: `['S3']`
- Selected: **S3**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 250 | — | $4.89 |
| requests | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 800 | — | $18.40 |

**SKU selection notes**

- Selected object storage SKU: earlydelete_int.
- Selected storage operations SKU: earlydelete_int.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 60
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 160
  - `memory`: 0.0167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 160
  - `monthly_gb_seconds`: 60
  - `monthly_memory_gib_hours`: 0.0167
  - `monthly_requests`: 800
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0083
  - `requests`: 800
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0083

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $     18.40
  Storage Cost           $      5.75
  Total                  $     20.53  (range $20.53–$27.77)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: earlydelete_int.; Selected storage operations SKU: earlydelete_int.

#### GCP — Cloud Storage

**Monthly estimate:** $8.51 – $11.52

**Service selection**
- Architecture options: `['Cloud Storage']`
- Selected: **Cloud Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | 0A5B-5BB2-9A38 | Cloud CDN Cache Fill from Europe to Middle East | $0.04000000 | GiBy | 250 | — | $8.50 |
| requests | 007A-40B7-63BC | Multi-Region Durable Reduced Availability Class A Operations | $0.00002000 | count | 800 | — | $0.02 |

**SKU selection notes**

- Selected object storage SKU: cdncachefill_ondemand.
- Selected storage operations SKU: draops_ondemand.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 60
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 160
  - `memory`: 0.0167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 160
  - `monthly_gb_seconds`: 60
  - `monthly_memory_gib_hours`: 0.0167
  - `monthly_requests`: 800
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0083
  - `requests`: 800
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0083

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.02
  Storage Cost           $     10.00
  Total                  $      8.51  (range $8.51–$11.52)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: cdncachefill_ondemand.; Selected storage operations SKU: draops_ondemand.

#### AZURE — Blob Storage

**Monthly estimate:** $13.16 – $17.80

**Service selection**
- Architecture options: `['Blob Storage']`
- Selected: **Blob Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z0BNWT/00CD | ZRS Data Stored | $0.06190000 | 1 GB/Month | 250 | — | $13.15 |
| requests | DZH318Z0CBTJ/05R9 | Smart Tier GRS Monitoring Operations | $0.04000000 | 10K | 800 | — | $32.00 |

**SKU selection notes**

- Selected object storage SKU: storage.
- Selected storage operations SKU: smart_tier_grs.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 60
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 160
  - `memory`: 0.0167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 160
  - `monthly_gb_seconds`: 60
  - `monthly_memory_gib_hours`: 0.0167
  - `monthly_requests`: 800
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0083
  - `requests`: 800
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0083

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $     15.47
  Total                  $     13.16  (range $13.16–$17.80)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: storage.; Selected storage operations SKU: smart_tier_grs.

---

### Component: Payments (`payment`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | N/A | $0.00–$0.00 | low |
| GCP | N/A | $0.00–$0.00 | low |
| AZURE | N/A | $0.00–$0.00 | low |

- Nominal (low) cost spread across providers: $0.00/month (aws=$0.00 vs aws=$0.00).
- Mapped equivalents: AWS=N/A, GCP=N/A, AZURE=N/A. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — N/A

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Stripe']`
- Selected: **None**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.
- Other options not used:
  - `Stripe`: listed in provider skip set (non-cloud / external)

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- Derived usage variables:

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Selection / default notes: cloud_service_option

#### GCP — N/A

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Stripe']`
- Selected: **None**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.
- Other options not used:
  - `Stripe`: listed in provider skip set (non-cloud / external)

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- Derived usage variables:

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Selection / default notes: cloud_service_option

#### AZURE — N/A

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Stripe']`
- Selected: **None**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.
- Other options not used:
  - `Stripe`: listed in provider skip set (non-cloud / external)

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- Derived usage variables:

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Selection / default notes: cloud_service_option

---

## Scenario: InsightAI

_AI document assistant, MVP, ~1,000 users with AI + background jobs_

- Users: **1000** | Stage: **mvp**
- Requirements: `{'auth': True, 'file_upload': True, 'background_processing': True, 'ai': True, 'dashboards': False, 'payments': False}`

### Component: Web App (`web_app`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Amplify Hosting | $0.30–$0.40 | medium |
| GCP | Firebase Hosting | $0.00–$0.00 | low |
| AZURE | Azure App Service | $127.50–$172.50 | medium |

- Nominal (low) cost spread across providers: $127.50/month (gcp=$0.00 vs azure=$127.50).
- Mapped equivalents: AWS=Amplify Hosting, GCP=Firebase Hosting, AZURE=Azure App Service. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs

#### AWS — Amplify Hosting

**Monthly estimate:** $0.30 – $0.40

**Service selection**
- Architecture options: `['Amplify Hosting']`
- Selected: **Amplify Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 250 | — | $0.01 |
| requests | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 6000 | — | $0.33 |

**SKU selection notes**

- Selected hosting storage SKU: requests.
- Selected hosting requests SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 450
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 450
  - `monthly_memory_gib_hours`: 0.125
  - `monthly_requests`: 6000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0625
  - `requests`: 6000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0625

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.33
  Storage Cost           $      0.01
  Total                  $      0.30  (range $0.30–$0.40)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: requests.; Selected hosting requests SKU: requests.

#### GCP — Firebase Hosting

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Firebase Hosting']`
- Selected: **Firebase Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No priced hosting storage SKU found in catalog.
- No priced hosting requests SKU found in catalog.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 450
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 450
  - `monthly_memory_gib_hours`: 0.125
  - `monthly_requests`: 6000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0625
  - `requests`: 6000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0625

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced hosting storage SKU found in catalog.; No priced hosting requests SKU found in catalog.; no_priced_skus:web_app
- Fuzzy / fallback matching:
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.

#### AZURE — Azure App Service

**Monthly estimate:** $127.50 – $172.50

**Service selection**
- Architecture options: `['Azure App Service']`
- Selected: **Azure App Service**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 250 | — | $5.10 |
| requests | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 6000 | — | $144.00 |

**SKU selection notes**

- Selected hosting storage SKU: standard.
- Selected hosting requests SKU: standard.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 450
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.125
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 450
  - `monthly_memory_gib_hours`: 0.125
  - `monthly_requests`: 6000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0625
  - `requests`: 6000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0625

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $    144.00
  Storage Cost           $      6.00
  Total                  $    127.50  (range $127.50–$172.50)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: standard.; Selected hosting requests SKU: standard.

---

### Component: API Gateway (`api_gateway`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | API Gateway | $0.00–$0.00 | medium |
| GCP | API Gateway | $0.04–$0.05 | low |
| AZURE | API Management | $0.04–$0.05 | low |

- Nominal (low) cost spread across providers: $0.04/month (aws=$0.00 vs gcp=$0.04).
- Mapped equivalents: AWS=API Gateway, GCP=API Gateway, AZURE=API Management. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: unusually high requests cost ($42000) — verify SKU/unit
  - AZURE: fallback or weak catalog match
  - AZURE: unusually high requests cost ($42000) — verify SKU/unit

#### AWS — API Gateway

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | FC2TWT2UEPTBKVBX | $1/million requests - API Gateway HTTP API (first 300 millio | $0.00000100 | Requests | 14000 | — | $0.01 |

**SKU selection notes**

- Selected API calls SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1050
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.2917
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 1050
  - `monthly_memory_gib_hours`: 0.2917
  - `monthly_requests`: 14000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.1458
  - `requests`: 14000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.1458

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected API calls SKU: requests.

#### GCP — API Gateway

**Monthly estimate:** $0.04 – $0.05

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 14000 | — | $42000.00 |

**SKU selection notes**

- No priced API calls SKU found in catalog.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1050
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.2917
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 1050
  - `monthly_memory_gib_hours`: 0.2917
  - `monthly_requests`: 14000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.1458
  - `requests`: 14000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.1458

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.04
  Total                  $      0.04  (range $0.04–$0.05)
```

**Confidence: LOW**

- Fallback pricing was used because the catalog lacked a suitable SKU.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced API calls SKU found in catalog.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.

#### AZURE — API Management

**Monthly estimate:** $0.04 – $0.05

**Service selection**
- Architecture options: `['API Management']`
- Selected: **API Management**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 14000 | — | $42000.00 |

**SKU selection notes**

- Selected API calls SKU: gateway.
- Ignored capacity/egress SKUs for API call pricing.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1050
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.2917
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 1050
  - `monthly_memory_gib_hours`: 0.2917
  - `monthly_requests`: 14000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.1458
  - `requests`: 14000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.1458

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.04
  Total                  $      0.04  (range $0.04–$0.05)
```

**Confidence: LOW**

- Fallback pricing was used because the catalog lacked a suitable SKU.
- Selection / default notes: Selected API calls SKU: gateway.; Ignored capacity/egress SKUs for API call pricing.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - Ignored capacity/egress SKUs for API call pricing.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - Ignored capacity/egress SKUs for API call pricing.
  - No API call SKU in catalog; using fallback $3.00/million requests.

---

### Component: API Service (`app_service`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Lambda | $0.00–$0.00 | medium |
| GCP | Cloud Run | $0.00–$0.01 | medium |
| AZURE | Functions | $0.03–$0.05 | medium |

- Nominal (low) cost spread across providers: $0.03/month (aws=$0.00 vs azure=$0.03).
- Mapped equivalents: AWS=Lambda, GCP=Cloud Run, AZURE=Functions. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Lambda

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Lambda']`
- Selected: **Lambda**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 12000 | — | $0.00 |
| execution | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 3000 | — | $0.00 |

**SKU selection notes**

- Selected requests SKU: requests.
- Selected gb-seconds SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.125

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Duration Cost          $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected requests SKU: requests.; Selected gb-seconds SKU: requests.

#### GCP — Cloud Run

**Monthly estimate:** $0.00 – $0.01

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.25 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 0.25 | — | $0.00 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 12000 | — | $0.00 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.125

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.01
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.01)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Functions

**Monthly estimate:** $0.03 – $0.05

**Service selection**
- Architecture options: `['Functions']`
- Selected: **Functions**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| execution | DZH318Z0DW2R/00BL | Always Ready Baseline | $0.00000500 | 1 GB Second | 3000 | — | $0.01 |
| cpu | DZH318Z0BXVK/000L | Premium vCPU Duration | $0.17500000 | 1 Hour | 0.25 | — | $0.04 |
| memory | DZH318Z0BXVK/000J | Premium Memory Duration | $0.01300000 | 1 GiB Hour | 0.25 | — | $0.00 |

**SKU selection notes**

- Selected execution SKU: always_ready.
- Selected cpu SKU: cpu.
- Selected memory SKU: memory.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.125

**Formula**

```
  Execution Cost = monthly_executions * skus.execution.unit_price_usd
  Vcpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Total = execution_cost + vcpu_cost + memory_cost
```

**Cost contribution**

```
  Execution Cost         $      0.02
  Vcpu Cost              $      0.02
  Memory Cost            $      0.00
  Total                  $      0.03  (range $0.03–$0.05)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected execution SKU: always_ready.; Selected cpu SKU: cpu.; Selected memory SKU: memory.

---

### Component: Job Worker (`queue_worker`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Lambda | $0.00–$0.00 | medium |
| GCP | Cloud Run | $0.00–$0.00 | medium |
| AZURE | Functions | $0.02–$0.02 | medium |

- Nominal (low) cost spread across providers: $0.02/month (aws=$0.00 vs azure=$0.02).
- Mapped equivalents: AWS=Lambda, GCP=Cloud Run, AZURE=Functions. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Lambda

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Lambda']`
- Selected: **Lambda**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 3200 | — | $0.00 |
| execution | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 3000 | — | $0.00 |

**SKU selection notes**

- Selected requests SKU: requests.
- Selected gb-seconds SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 240
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 240
  - `monthly_memory_gib_hours`: 0.0667
  - `monthly_requests`: 3200
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0333
  - `requests`: 3200
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0333

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Duration Cost          $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected requests SKU: requests.; Selected gb-seconds SKU: requests.

#### GCP — Cloud Run

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.25 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 0.0667 | — | $0.00 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 3200 | — | $0.00 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 240
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 240
  - `monthly_memory_gib_hours`: 0.0667
  - `monthly_requests`: 3200
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0333
  - `requests`: 3200
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0333

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.00
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Functions

**Monthly estimate:** $0.02 – $0.02

**Service selection**
- Architecture options: `['Functions']`
- Selected: **Functions**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| execution | DZH318Z0DW2R/00BL | Always Ready Baseline | $0.00000500 | 1 GB Second | 3000 | — | $0.01 |
| cpu | DZH318Z0BXVK/000L | Premium vCPU Duration | $0.17500000 | 1 Hour | 0.25 | — | $0.04 |
| memory | DZH318Z0BXVK/000J | Premium Memory Duration | $0.01300000 | 1 GiB Hour | 0.0667 | — | $0.00 |

**SKU selection notes**

- Selected execution SKU: always_ready.
- Selected cpu SKU: cpu.
- Selected memory SKU: memory.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 240
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 240
  - `monthly_memory_gib_hours`: 0.0667
  - `monthly_requests`: 3200
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0333
  - `requests`: 3200
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0333

**Formula**

```
  Execution Cost = monthly_executions * skus.execution.unit_price_usd
  Vcpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Total = execution_cost + vcpu_cost + memory_cost
```

**Cost contribution**

```
  Execution Cost         $      0.02
  Vcpu Cost              $      0.01
  Memory Cost            $      0.00
  Total                  $      0.02  (range $0.02–$0.02)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected execution SKU: always_ready.; Selected cpu SKU: cpu.; Selected memory SKU: memory.

---

### Component: Message Queue (`queue`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | SQS | $0.00–$0.00 | medium |
| GCP | Cloud Pub/Sub | $0.00–$0.00 | low |
| AZURE | Service Bus | $0.00–$0.00 | medium |

- Nominal (low) cost spread across providers: $0.00/month (aws=$0.00 vs aws=$0.00).
- Mapped equivalents: AWS=SQS, GCP=Cloud Pub/Sub, AZURE=Service Bus. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: unusually high requests cost ($1280) — verify SKU/unit

#### AWS — SQS

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['SQS']`
- Selected: **SQS**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | VUY9G3EK3YXBUD92 | $0.10 per million Amazon SQS fair queue requests in US East  | $0.00000010 | Requests | 3200 | — | $0.00 |

**SKU selection notes**

- Selected queue messages SKU: requests.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 240
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 240
  - `monthly_memory_gib_hours`: 0.0667
  - `monthly_requests`: 3200
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0333
  - `requests`: 3200
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0333

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected queue messages SKU: requests.

#### GCP — Cloud Pub/Sub

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Pub/Sub']`
- Selected: **Cloud Pub/Sub**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback queue message pricing | $0.40000000 | 1M requests | 3200 | — | $1280.00 |

**SKU selection notes**

- Selected queue messages SKU: subscription_ondemand.
- Ignored non-message queue SKU: subscription_ondemand.
- No queue message SKU in catalog; using fallback $0.40/million messages.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 240
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 240
  - `monthly_memory_gib_hours`: 0.0667
  - `monthly_requests`: 3200
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0333
  - `requests`: 3200
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0333

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- Computed monthly cost is zero.
- Fallback pricing was used because the catalog lacked a suitable SKU.
- Selection / default notes: Selected queue messages SKU: subscription_ondemand.; Ignored non-message queue SKU: subscription_ondemand.; No queue message SKU in catalog; using fallback $0.40/million messages.
- Fuzzy / fallback matching:
  - Ignored non-message queue SKU: subscription_ondemand.
  - No queue message SKU in catalog; using fallback $0.40/million messages.
  - Ignored non-message queue SKU: subscription_ondemand.
  - No queue message SKU in catalog; using fallback $0.40/million messages.

#### AZURE — Service Bus

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Service Bus']`
- Selected: **Service Bus**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | DZH318Z0BQN0/00W9 | WCF Relay Message | $0.01100000 | 10K | 3200 | — | $35.20 |

**SKU selection notes**

- Selected queue messages SKU: wcf_relay.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 240
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 240
  - `monthly_memory_gib_hours`: 0.0667
  - `monthly_requests`: 3200
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0333
  - `requests`: 3200
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0333

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected queue messages SKU: wcf_relay.

---

### Component: Document Storage (`object_storage`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | S3 | $20.53–$27.77 | medium |
| GCP | Cloud Storage | $8.51–$11.52 | medium |
| AZURE | Blob Storage | $13.16–$17.80 | medium |

- Nominal (low) cost spread across providers: $12.02/month (gcp=$8.51 vs aws=$20.53).
- Mapped equivalents: AWS=S3, GCP=Cloud Storage, AZURE=Blob Storage. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — S3

**Monthly estimate:** $20.53 – $27.77

**Service selection**
- Architecture options: `['S3']`
- Selected: **S3**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 250 | — | $4.89 |
| requests | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 800 | — | $18.40 |

**SKU selection notes**

- Selected object storage SKU: earlydelete_int.
- Selected storage operations SKU: earlydelete_int.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 60
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 60
  - `monthly_memory_gib_hours`: 0.0167
  - `monthly_requests`: 800
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0083
  - `requests`: 800
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0083

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $     18.40
  Storage Cost           $      5.75
  Total                  $     20.53  (range $20.53–$27.77)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: earlydelete_int.; Selected storage operations SKU: earlydelete_int.

#### GCP — Cloud Storage

**Monthly estimate:** $8.51 – $11.52

**Service selection**
- Architecture options: `['Cloud Storage']`
- Selected: **Cloud Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | 0A5B-5BB2-9A38 | Cloud CDN Cache Fill from Europe to Middle East | $0.04000000 | GiBy | 250 | — | $8.50 |
| requests | 007A-40B7-63BC | Multi-Region Durable Reduced Availability Class A Operations | $0.00002000 | count | 800 | — | $0.02 |

**SKU selection notes**

- Selected object storage SKU: cdncachefill_ondemand.
- Selected storage operations SKU: draops_ondemand.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 60
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 60
  - `monthly_memory_gib_hours`: 0.0167
  - `monthly_requests`: 800
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0083
  - `requests`: 800
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0083

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.02
  Storage Cost           $     10.00
  Total                  $      8.51  (range $8.51–$11.52)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: cdncachefill_ondemand.; Selected storage operations SKU: draops_ondemand.

#### AZURE — Blob Storage

**Monthly estimate:** $13.16 – $17.80

**Service selection**
- Architecture options: `['Blob Storage']`
- Selected: **Blob Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z0BNWT/00CD | ZRS Data Stored | $0.06190000 | 1 GB/Month | 250 | — | $13.15 |
| requests | DZH318Z0CBTJ/05R9 | Smart Tier GRS Monitoring Operations | $0.04000000 | 10K | 800 | — | $32.00 |

**SKU selection notes**

- Selected object storage SKU: storage.
- Selected storage operations SKU: smart_tier_grs.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 60
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 60
  - `monthly_memory_gib_hours`: 0.0167
  - `monthly_requests`: 800
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0083
  - `requests`: 800
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0083

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $     15.47
  Total                  $     13.16  (range $13.16–$17.80)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: storage.; Selected storage operations SKU: smart_tier_grs.

---

### Component: AI Inference (`ai_provider`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Bedrock | $0.87–$1.17 | medium |
| GCP | Vertex AI | $217.90–$294.81 | medium |
| AZURE | Foundry Models | $84.15–$113.85 | medium |

- Nominal (low) cost spread across providers: $217.03/month (aws=$0.87 vs gcp=$217.90).
- Mapped equivalents: AWS=Bedrock, GCP=Vertex AI, AZURE=Foundry Models. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Bedrock

**Monthly estimate:** $0.87 – $1.17

**Service selection**
- Architecture options: `['Bedrock']`
- Selected: **Bedrock**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| inference | 3NRMZNF7G8SFHU4N | $0.00017 per 1K input tokens for Llama 4 Scout 17B in US Eas | $0.00017000 | 1K tokens | 6e+06 | — | $0.87 |

**SKU selection notes**

- Selected on-demand inference SKU: use1_llama4_scout_17b_input_tokens.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Inference Cost = (monthly_tokens / 1000) * skus.inference.unit_price_usd
  Total = inference_cost
```

**Cost contribution**

```
  Inference Cost         $      1.02
  Total                  $      0.87  (range $0.87–$1.17)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected on-demand inference SKU: use1_llama4_scout_17b_input_tokens.

#### GCP — Vertex AI

**Monthly estimate:** $217.90 – $294.81

**Service selection**
- Architecture options: `['Vertex AI']`
- Selected: **Vertex AI**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| inference | 0119-74FE-BD3A | Vertex Colab CPU for GCE usage - A2 Instance Cores in us-eas | $0.04272600 | h | 730 | — | $217.90 |

**SKU selection notes**

- Selected on-demand inference SKU: cpu.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Inference Cost = (monthly_tokens / 1000) * skus.inference.unit_price_usd
  Total = inference_cost
```

**Cost contribution**

```
  Inference Cost         $    256.36
  Total                  $    217.90  (range $217.90–$294.81)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected on-demand inference SKU: cpu.

#### AZURE — Foundry Models

**Monthly estimate:** $84.15 – $113.85

**Service selection**
- Architecture options: `['Foundry Models']`
- Selected: **Foundry Models**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| inference | DZH318Z0T9WD/0HNH | 5.4 opt Dz 1M Tokens | $16.50000000 | 1M | 6e+06 | — | $84.15 |

**SKU selection notes**

- Selected on-demand inference SKU: tokens.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Inference Cost = (monthly_tokens / 1000000) * skus.inference.unit_price_usd
  Total = inference_cost
```

**Cost contribution**

```
  Inference Cost         $     99.00
  Total                  $     84.15  (range $84.15–$113.85)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected on-demand inference SKU: tokens.

---

### Component: Metadata DB (`database`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | DynamoDB | $21.25–$28.75 | medium |
| GCP | Cloud Firestore | $0.00–$0.00 | low |
| AZURE | Azure Cosmos DB | $10.63–$14.38 | medium |

- Nominal (low) cost spread across providers: $21.25/month (gcp=$0.00 vs aws=$21.25).
- Mapped equivalents: AWS=DynamoDB, GCP=Cloud Firestore, AZURE=Azure Cosmos DB. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs

#### AWS — DynamoDB

**Monthly estimate:** $21.25 – $28.75

**Service selection**
- Architecture options: `['DynamoDB']`
- Selected: **DynamoDB**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | 4W4ZMC46EHE8XTTZ | $0.125 per million read request units (N. Virginia) | $0.00000012 | ReadRequestUnits | 2000 | — | $0.00 |
| storage | 3ADXMU9RYGKRUA9W | $0.10000 per GB of data exported in US East (N. Virginia) | $0.10000000 | GB | 250 | — | $21.25 |

**SKU selection notes**

- Selected read/write requests SKU: requests.
- Selected storage SKU: use1_exportdatasize_bytes.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $     25.00
  Total                  $     21.25  (range $21.25–$28.75)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected read/write requests SKU: requests.; Selected storage SKU: use1_exportdatasize_bytes.

#### GCP — Cloud Firestore

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Firestore']`
- Selected: **Cloud Firestore**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No read/write requests SKU found in catalog.
- No priced storage SKU found in catalog.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No read/write requests SKU found in catalog.; No priced storage SKU found in catalog.; no_priced_skus:database
- Fuzzy / fallback matching:
  - No priced storage SKU found in catalog.
  - No priced storage SKU found in catalog.

#### AZURE — Azure Cosmos DB

**Monthly estimate:** $10.63 – $14.38

**Service selection**
- Architecture options: `['Azure Cosmos DB']`
- Selected: **Azure Cosmos DB**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | DZH318Z0CDGF/0019 | Standard Read Operations | $0.00400000 | 10K | 2000 | — | $8.00 |
| storage | DZH318Z0CF60/0005 | 256 GiB Disk | $0.05000000 | 1/Hour | 250 | — | $10.62 |

**SKU selection notes**

- Selected read/write requests SKU: standard.
- Selected storage SKU: memory.

**Usage assumptions**

- expected_users: 1000
- user_count: 1000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 150
  - `egress`: 24
  - `egress_gb`: 24
  - `execution`: 3000
  - `memory`: 0.0417
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 3000
  - `monthly_auth_events`: 8000
  - `monthly_executions`: 3000
  - `monthly_gb_seconds`: 150
  - `monthly_memory_gib_hours`: 0.0417
  - `monthly_requests`: 2000
  - `monthly_tokens`: 6e+06
  - `monthly_vcpu_hours`: 0.0208
  - `requests`: 2000
  - `storage`: 250
  - `storage_gib`: 250
  - `vcpu`: 0.0208

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $     12.50
  Total                  $     10.63  (range $10.63–$14.38)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected read/write requests SKU: standard.; Selected storage SKU: memory.

---

## Scenario: HealthPortal

_Healthcare patient portal, production scale, ~10,000 users_

- Users: **10000** | Stage: **production**
- Requirements: `{'auth': True, 'file_upload': True, 'background_processing': False, 'ai': False, 'dashboards': True, 'payments': False}`

### Component: Patient Portal (`web_app`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Amplify Hosting | $8.74–$11.82 | medium |
| GCP | Firebase Hosting | $0.00–$0.00 | low |
| AZURE | Azure App Service | $3774.00–$5106.00 | medium |

- Nominal (low) cost spread across providers: $3774.00/month (gcp=$0.00 vs azure=$3774.00).
- Mapped equivalents: AWS=Amplify Hosting, GCP=Firebase Hosting, AZURE=Azure App Service. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs
  - AZURE: unusually high requests cost ($4320) — verify SKU/unit

#### AWS — Amplify Hosting

**Monthly estimate:** $8.74 – $11.82

**Service selection**
- Architecture options: `['Amplify Hosting']`
- Selected: **Amplify Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 5000 | — | $0.24 |
| requests | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 180000 | — | $10.00 |

**SKU selection notes**

- Selected hosting storage SKU: requests.
- Selected hosting requests SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 63000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 36000
  - `memory`: 17.5
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 36000
  - `monthly_gb_seconds`: 63000
  - `monthly_memory_gib_hours`: 17.5
  - `monthly_requests`: 180000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 8.75
  - `requests`: 180000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 8.75

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $     10.00
  Storage Cost           $      0.28
  Total                  $      8.74  (range $8.74–$11.82)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: requests.; Selected hosting requests SKU: requests.

#### GCP — Firebase Hosting

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Firebase Hosting']`
- Selected: **Firebase Hosting**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No priced hosting storage SKU found in catalog.
- No priced hosting requests SKU found in catalog.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 63000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 36000
  - `memory`: 17.5
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 36000
  - `monthly_gb_seconds`: 63000
  - `monthly_memory_gib_hours`: 17.5
  - `monthly_requests`: 180000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 8.75
  - `requests`: 180000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 8.75

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced hosting storage SKU found in catalog.; No priced hosting requests SKU found in catalog.; no_priced_skus:web_app
- Fuzzy / fallback matching:
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.

#### AZURE — Azure App Service

**Monthly estimate:** $3774.00 – $5106.00

**Service selection**
- Architecture options: `['Azure App Service']`
- Selected: **Azure App Service**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 5000 | — | $102.00 |
| requests | DZH318Z08W5K/0001 | Standard Azure Front Door Add-on | $0.02400000 | 1 Hour | 180000 | — | $4320.00 |

**SKU selection notes**

- Selected hosting storage SKU: standard.
- Selected hosting requests SKU: standard.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 63000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 36000
  - `memory`: 17.5
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 36000
  - `monthly_gb_seconds`: 63000
  - `monthly_memory_gib_hours`: 17.5
  - `monthly_requests`: 180000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 8.75
  - `requests`: 180000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 8.75

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $   4320.00
  Storage Cost           $    120.00
  Total                  $   3774.00  (range $3774.00–$5106.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: standard.; Selected hosting requests SKU: standard.

---

### Component: Load Balancer (`load_balancer`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Application Load Balancer | $101.25–$101.25 | medium |
| GCP | Networking | $540.00–$540.00 | medium |
| AZURE | Application Gateway | $635.04–$635.04 | medium |

- Nominal (low) cost spread across providers: $533.79/month (aws=$101.25 vs azure=$635.04).
- Mapped equivalents: AWS=Application Load Balancer, GCP=Networking, AZURE=Application Gateway. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Application Load Balancer

**Monthly estimate:** $101.25 – $101.25

**Service selection**
- Architecture options: `['Application Load Balancer']`
- Selected: **Application Load Balancer**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | YKBGGP5EBGDU9T5W | $0.0225 per Network LoadBalancer-hour (or partial hour) | $0.02250000 | Hrs | 600 | — | $101.25 |

**SKU selection notes**

- Selected CDN egress SKU: elb_balancing.
- CDN egress assumed 4500.0 GiB/month for 10000 users.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 42000
  - `egress`: 600
  - `egress_gb`: 4500
  - `execution`: 24000
  - `memory`: 11.6667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 24000
  - `monthly_gb_seconds`: 42000
  - `monthly_memory_gib_hours`: 11.6667
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 5.8333
  - `requests`: 120000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 5.8333

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $    101.25
  Total                  $    101.25  (range $101.25–$101.25)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: elb_balancing.; CDN egress assumed 4500.0 GiB/month for 10000 users.

#### GCP — Networking

**Monthly estimate:** $540.00 – $540.00

**Service selection**
- Architecture options: `['Networking']`
- Selected: **Networking**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | 307A-FED8-5B99 | Networking Data Transfer inter region Intercontinental (Excl | $0.12000000 | GiBy | 600 | — | $540.00 |

**SKU selection notes**

- Selected CDN egress SKU: datatransfer_ondemand.
- CDN egress assumed 4500.0 GiB/month for 10000 users.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 42000
  - `egress`: 600
  - `egress_gb`: 4500
  - `execution`: 24000
  - `memory`: 11.6667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 24000
  - `monthly_gb_seconds`: 42000
  - `monthly_memory_gib_hours`: 11.6667
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 5.8333
  - `requests`: 120000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 5.8333

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $    540.00
  Total                  $    540.00  (range $540.00–$540.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: datatransfer_ondemand.; CDN egress assumed 4500.0 GiB/month for 10000 users.

#### AZURE — Application Gateway

**Monthly estimate:** $635.04 – $635.04

**Service selection**
- Architecture options: `['Application Gateway']`
- Selected: **Application Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | DZH318Z0BNVT/0020 | Medium Gateway | $0.14112000 | 1 Hour | 600 | — | $635.04 |

**SKU selection notes**

- Selected CDN egress SKU: medium.
- CDN egress assumed 4500.0 GiB/month for 10000 users.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 42000
  - `egress`: 600
  - `egress_gb`: 4500
  - `execution`: 24000
  - `memory`: 11.6667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 24000
  - `monthly_gb_seconds`: 42000
  - `monthly_memory_gib_hours`: 11.6667
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 5.8333
  - `requests`: 120000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 5.8333

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $    635.04
  Total                  $    635.04  (range $635.04–$635.04)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: medium.; CDN egress assumed 4500.0 GiB/month for 10000 users.

---

### Component: API Gateway (`api_gateway`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | API Gateway | $0.00–$0.00 | low |
| GCP | API Gateway | $1.07–$1.45 | low |
| AZURE | API Management | $300.00–$300.00 | medium |

- Nominal (low) cost spread across providers: $300.00/month (aws=$0.00 vs azure=$300.00).
- Mapped equivalents: AWS=API Gateway, GCP=API Gateway, AZURE=API Management. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - AWS: fallback or weak catalog match
  - GCP: fallback or weak catalog match
  - GCP: unusually high requests cost ($1260000) — verify SKU/unit

#### AWS — API Gateway

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | FC2TWT2UEPTBKVBX | $1/million requests - API Gateway HTTP API (first 300 millio | $0.00000100 | Requests | 420000 | — | $0.42 |

**SKU selection notes**

- No priced gateway capacity unit SKU found in catalog.
- Selected API calls SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 147000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 84000
  - `memory`: 40.8333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 84000
  - `monthly_gb_seconds`: 147000
  - `monthly_memory_gib_hours`: 40.8333
  - `monthly_requests`: 420000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 20.4167
  - `requests`: 420000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 20.4167

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced gateway capacity unit SKU found in catalog.; Selected API calls SKU: requests.
- Fuzzy / fallback matching:
  - No priced gateway capacity unit SKU found in catalog.
  - No priced gateway capacity unit SKU found in catalog.

#### GCP — API Gateway

**Monthly estimate:** $1.07 – $1.45

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 420000 | — | $1260000.00 |

**SKU selection notes**

- No priced gateway capacity unit SKU found in catalog.
- No priced API calls SKU found in catalog.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 147000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 84000
  - `memory`: 40.8333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 84000
  - `monthly_gb_seconds`: 147000
  - `monthly_memory_gib_hours`: 40.8333
  - `monthly_requests`: 420000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 20.4167
  - `requests`: 420000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 20.4167

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      1.26
  Total                  $      1.07  (range $1.07–$1.45)
```

**Confidence: LOW**

- Fallback pricing was used because the catalog lacked a suitable SKU.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced gateway capacity unit SKU found in catalog.; No priced API calls SKU found in catalog.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - No priced gateway capacity unit SKU found in catalog.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - No priced gateway capacity unit SKU found in catalog.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.

#### AZURE — API Management

**Monthly estimate:** $300.00 – $300.00

**Service selection**
- Architecture options: `['API Management']`
- Selected: **API Management**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | DZH318Z0BQCM/00QT | Basic v2 Secondary Unit | $0.20548000 | 1 Hour | 730 | — | $300.00 |

**SKU selection notes**

- Selected gateway capacity unit SKU: basic_v2.
- API gateway sized at 2 capacity unit(s).

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 147000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 84000
  - `gateway_units`: 2
  - `instance_billable_units`: 730
  - `memory`: 40.8333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 84000
  - `monthly_gb_seconds`: 147000
  - `monthly_memory_gib_hours`: 40.8333
  - `monthly_requests`: 420000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 20.4167
  - `requests`: 420000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 20.4167

**Formula**

```
  Instance Cost = gateway_units * instance_billable_units * skus.instance.unit_price_usd
  Total = instance_cost
```

**Cost contribution**

```
  Instance Cost          $    300.00
  Total                  $    300.00  (range $300.00–$300.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected gateway capacity unit SKU: basic_v2.; API gateway sized at 2 capacity unit(s).

---

### Component: Core API (`app_service`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | ECS Fargate | $1836.23–$2484.31 | medium |
| GCP | Cloud Run | $0.60–$0.81 | medium |
| AZURE | Azure Container Apps | $0.12–$0.17 | low |

- Nominal (low) cost spread across providers: $1836.11/month (azure=$0.12 vs aws=$1836.23).
- Mapped equivalents: AWS=ECS Fargate, GCP=Cloud Run, AZURE=Azure Container Apps. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - AZURE: fallback or weak catalog match

#### AWS — ECS Fargate

**Monthly estimate:** $1836.23 – $2484.31

**Service selection**
- Architecture options: `['ECS Fargate']`
- Selected: **ECS Fargate**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | PBZNQUSEXZUC34C9 | AWS Fargate - Memory  - US East (N.Virginia) | $0.00444500 | hours | 360000 | — | $1600.20 |
| execution | PBZNQUSEXZUC34C9 | AWS Fargate - Memory  - US East (N.Virginia) | $0.00444500 | hours | 72000 | — | $320.04 |

**SKU selection notes**

- Selected requests SKU: memory.
- Selected gb-seconds SKU: memory.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 126000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 72000
  - `memory`: 35
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 72000
  - `monthly_gb_seconds`: 126000
  - `monthly_memory_gib_hours`: 35
  - `monthly_requests`: 360000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 17.5
  - `requests`: 360000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 17.5

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $   1600.20
  Duration Cost          $    560.07
  Total                  $   1836.23  (range $1836.23–$2484.31)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected requests SKU: memory.; Selected gb-seconds SKU: memory.

#### GCP — Cloud Run

**Monthly estimate:** $0.60 – $0.81

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.5 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 35 | — | $0.59 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 360000 | — | $0.12 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 126000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 72000
  - `memory`: 35
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 72000
  - `monthly_gb_seconds`: 126000
  - `monthly_memory_gib_hours`: 35
  - `monthly_requests`: 360000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 17.5
  - `requests`: 360000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 17.5

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.70
  Request Cost           $      0.00
  Total                  $      0.60  (range $0.60–$0.81)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Azure Container Apps

**Monthly estimate:** $0.12 – $0.17

**Service selection**
- Architecture options: `['Azure Container Apps']`
- Selected: **Azure Container Apps**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | DZH318Z0B0NC/004Q | Standard vCPU Active Usage | $0.00003400 | 1 Second | 0.5 | — | $0.00 |
| requests | DZH318Z0B0NC/0026 | Standard Requests | $0.40000000 | 1M | 360000 | — | $144000.00 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- No priced memory SKU found in catalog.
- Selected requests SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 126000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 72000
  - `memory`: 35
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 72000
  - `monthly_gb_seconds`: 126000
  - `monthly_memory_gib_hours`: 35
  - `monthly_requests`: 360000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 17.5
  - `requests`: 360000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 17.5

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Request Cost           $      0.14
  Total                  $      0.12  (range $0.12–$0.17)
```

**Confidence: LOW**

- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: Selected cpu SKU: cpu.; No priced memory SKU found in catalog.; Selected requests SKU: requests.
- Fuzzy / fallback matching:
  - No priced memory SKU found in catalog.
  - No priced memory SKU found in catalog.

---

### Component: Identity (`auth`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Cognito | $0.00–$0.00 | low |
| GCP | Identity Platform | $0.00–$0.00 | low |
| AZURE | Entra ID B2C | $0.00–$0.00 | low |

- Nominal (low) cost spread across providers: $0.00/month (aws=$0.00 vs aws=$0.00).
- Mapped equivalents: AWS=Cognito, GCP=Identity Platform, AZURE=Entra ID B2C. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - AWS: $0 — likely missing catalog or SKUs
  - GCP: $0 — likely missing catalog or SKUs
  - AZURE: $0 — likely missing catalog or SKUs

#### AWS — Cognito

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cognito']`
- Selected: **Cognito**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 42000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 24000
  - `memory`: 11.6667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 24000
  - `monthly_gb_seconds`: 42000
  - `monthly_memory_gib_hours`: 11.6667
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 5.8333
  - `requests`: 120000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 5.8333

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:aws:Cognito

#### GCP — Identity Platform

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Identity Platform']`
- Selected: **Identity Platform**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 42000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 24000
  - `memory`: 11.6667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 24000
  - `monthly_gb_seconds`: 42000
  - `monthly_memory_gib_hours`: 11.6667
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 5.8333
  - `requests`: 120000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 5.8333

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:gcp:Identity Platform

#### AZURE — Entra ID B2C

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Entra ID B2C']`
- Selected: **Entra ID B2C**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.1
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 42000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 24000
  - `memory`: 11.6667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 24000
  - `monthly_gb_seconds`: 42000
  - `monthly_memory_gib_hours`: 11.6667
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 5.8333
  - `requests`: 120000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 5.8333

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:azure:Entra ID B2C

---

### Component: Patient Records (`database`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | RDS | $640.75–$828.25 | medium |
| GCP | Cloud SQL | $90.16–$111.16 | medium |
| AZURE | SQL Database | $2449.50–$3306.30 | medium |

- Nominal (low) cost spread across providers: $2359.34/month (gcp=$90.16 vs azure=$2449.50).
- Mapped equivalents: AWS=RDS, GCP=Cloud SQL, AZURE=SQL Database. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — RDS

**Monthly estimate:** $640.75 – $828.25

**Service selection**
- Architecture options: `['RDS']`
- Selected: **RDS**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | K4SGPVDGPSJ8UZVP | USD 0.150 per db.t3.medium Single-AZ instance hour (or parti | $0.15000000 | Hrs | 730 | — | $109.50 |
| storage | 84K7WYHA9BB4ZQU3 | USD 0.125 per GB-Month of provisioned io2 storage for Single | $0.12500000 | GB-Mo | 5000 | — | $531.25 |

**SKU selection notes**

- Selected instance tier SKU: instanceusage_db_t3_medium (target tier 4).
- Selected storage SKU: storage.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 21000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 12000
  - `instance_billable_units`: 730
  - `memory`: 5.8333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 12000
  - `monthly_gb_seconds`: 21000
  - `monthly_memory_gib_hours`: 5.8333
  - `monthly_requests`: 60000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 2.9167
  - `requests`: 60000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 2.9167

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = instance_cost + storage_cost
```

**Cost contribution**

```
  Instance Cost          $    109.50
  Storage Cost           $    625.00
  Total                  $    640.75  (range $640.75–$828.25)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected instance tier SKU: instanceusage_db_t3_medium (target tier 4).; Selected storage SKU: storage.

#### GCP — Cloud SQL

**Monthly estimate:** $90.16 – $111.16

**Service selection**
- Architecture options: `['Cloud SQL']`
- Selected: **Cloud SQL**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | 00FF-CE73-9FEC | Cloud SQL for PostgreSQL: Regional - Extended support f1-mic | $0.04200000 | h | 730 | — | $30.66 |
| storage | 0023-A861-3E87 | Cloud SQL for MySQL: Regional - RAM in Phoenix | $0.01400000 | GiBy.h | 5000 | — | $59.50 |

**SKU selection notes**

- Selected instance tier SKU: sqlgen2instancesf1micro_ondemand (target tier 4).
- Selected storage SKU: memory.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 21000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 12000
  - `instance_billable_units`: 730
  - `memory`: 5.8333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 12000
  - `monthly_gb_seconds`: 21000
  - `monthly_memory_gib_hours`: 5.8333
  - `monthly_requests`: 60000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 2.9167
  - `requests`: 60000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 2.9167

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = instance_cost + storage_cost
```

**Cost contribution**

```
  Instance Cost          $     30.66
  Storage Cost           $     70.00
  Total                  $     90.16  (range $90.16–$111.16)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected instance tier SKU: sqlgen2instancesf1micro_ondemand (target tier 4).; Selected storage SKU: memory.

#### AZURE — SQL Database

**Monthly estimate:** $2449.50 – $3306.30

**Service selection**
- Architecture options: `['SQL Database']`
- Selected: **SQL Database**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | DZH318Z0BQHF/027T | S1 Secondary DTUs | $0.73000000 | 1/Day | 1 | — | $21.90 |
| storage | DZH318Z0BQCL/002Z | Data Stored | $0.57120000 | 1 GB/Month | 5000 | — | $2427.60 |

**SKU selection notes**

- Selected instance tier SKU: s1_secondary (target tier 4).
- Selected storage SKU: storage.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 21000
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 12000
  - `instance_billable_units`: 30
  - `memory`: 5.8333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 12000
  - `monthly_gb_seconds`: 21000
  - `monthly_memory_gib_hours`: 5.8333
  - `monthly_requests`: 60000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 2.9167
  - `requests`: 60000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 2.9167

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = instance_cost + storage_cost
```

**Cost contribution**

```
  Instance Cost          $     21.90
  Storage Cost           $   2856.00
  Total                  $   2449.50  (range $2449.50–$3306.30)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected instance tier SKU: s1_secondary (target tier 4).; Selected storage SKU: storage.

---

### Component: Medical Files (`object_storage`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | S3 | $566.95–$767.05 | medium |
| GCP | Cloud Storage | $170.41–$230.55 | medium |
| AZURE | Blob Storage | $263.16–$356.04 | medium |

- Nominal (low) cost spread across providers: $396.54/month (gcp=$170.41 vs aws=$566.95).
- Mapped equivalents: AWS=S3, GCP=Cloud Storage, AZURE=Blob Storage. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — S3

**Monthly estimate:** $566.95 – $767.05

**Service selection**
- Architecture options: `['S3']`
- Selected: **S3**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 5000 | — | $97.75 |
| requests | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 24000 | — | $552.00 |

**SKU selection notes**

- Selected object storage SKU: earlydelete_int.
- Selected storage operations SKU: earlydelete_int.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 8400
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 4800
  - `memory`: 2.3333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 4800
  - `monthly_gb_seconds`: 8400
  - `monthly_memory_gib_hours`: 2.3333
  - `monthly_requests`: 24000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.1667
  - `requests`: 24000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 1.1667

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $    552.00
  Storage Cost           $    115.00
  Total                  $    566.95  (range $566.95–$767.05)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: earlydelete_int.; Selected storage operations SKU: earlydelete_int.

#### GCP — Cloud Storage

**Monthly estimate:** $170.41 – $230.55

**Service selection**
- Architecture options: `['Cloud Storage']`
- Selected: **Cloud Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | 0A5B-5BB2-9A38 | Cloud CDN Cache Fill from Europe to Middle East | $0.04000000 | GiBy | 5000 | — | $170.00 |
| requests | 007A-40B7-63BC | Multi-Region Durable Reduced Availability Class A Operations | $0.00002000 | count | 24000 | — | $0.48 |

**SKU selection notes**

- Selected object storage SKU: cdncachefill_ondemand.
- Selected storage operations SKU: draops_ondemand.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 8400
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 4800
  - `memory`: 2.3333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 4800
  - `monthly_gb_seconds`: 8400
  - `monthly_memory_gib_hours`: 2.3333
  - `monthly_requests`: 24000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.1667
  - `requests`: 24000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 1.1667

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.48
  Storage Cost           $    200.00
  Total                  $    170.41  (range $170.41–$230.55)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: cdncachefill_ondemand.; Selected storage operations SKU: draops_ondemand.

#### AZURE — Blob Storage

**Monthly estimate:** $263.16 – $356.04

**Service selection**
- Architecture options: `['Blob Storage']`
- Selected: **Blob Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z0BNWT/00CD | ZRS Data Stored | $0.06190000 | 1 GB/Month | 5000 | — | $263.07 |
| requests | DZH318Z0CBTJ/05R9 | Smart Tier GRS Monitoring Operations | $0.04000000 | 10K | 24000 | — | $960.00 |

**SKU selection notes**

- Selected object storage SKU: storage.
- Selected storage operations SKU: smart_tier_grs.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 8400
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 4800
  - `memory`: 2.3333
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 4800
  - `monthly_gb_seconds`: 8400
  - `monthly_memory_gib_hours`: 2.3333
  - `monthly_requests`: 24000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.1667
  - `requests`: 24000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 1.1667

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.10
  Storage Cost           $    309.50
  Total                  $    263.16  (range $263.16–$356.04)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: storage.; Selected storage operations SKU: smart_tier_grs.

---

### Component: Monitoring (`monitoring`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | CloudWatch | $0.00–$0.00 | medium |
| GCP | Cloud Monitoring | $0.00–$0.00 | medium |
| AZURE | Azure Monitor | $10.00–$10.00 | medium |

- Nominal (low) cost spread across providers: $10.00/month (aws=$0.00 vs azure=$10.00).
- Mapped equivalents: AWS=CloudWatch, GCP=Cloud Monitoring, AZURE=Azure Monitor. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — CloudWatch

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['CloudWatch']`
- Selected: **CloudWatch**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | HBN93D4THS5J5RB6 | $0.00000001 per Samples Scanned for CW:PromQL:SamplesScanned | $0.00000001 | Samples Scanned | 12000 | — | $0.00 |

**SKU selection notes**

- Selected log/metric ingestion SKU: cw_promql_samplesscanned.
- Assumed 10.0 GiB log/metric ingestion per month.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.01
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 4200
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 2400
  - `log_ingestion_gb`: 10
  - `memory`: 1.1667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 2400
  - `monthly_gb_seconds`: 4200
  - `monthly_memory_gib_hours`: 1.1667
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.5833
  - `requests`: 12000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 0.5833

**Formula**

```
  Ingestion Cost = log_ingestion_gb * skus.requests.unit_price_usd
  Total = ingestion_cost
```

**Cost contribution**

```
  Ingestion Cost         $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected log/metric ingestion SKU: cw_promql_samplesscanned.; Assumed 10.0 GiB log/metric ingestion per month.

#### GCP — Cloud Monitoring

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Monitoring']`
- Selected: **Cloud Monitoring**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | 55A9-89F6-775B | Workload Metrics Samples Ingested | $0.00000015 | count | 12000 | — | $0.00 |

**SKU selection notes**

- Selected log/metric ingestion SKU: monitoring_ondemand.
- Assumed 10.0 GiB log/metric ingestion per month.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.01
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 4200
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 2400
  - `log_ingestion_gb`: 10
  - `memory`: 1.1667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 2400
  - `monthly_gb_seconds`: 4200
  - `monthly_memory_gib_hours`: 1.1667
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.5833
  - `requests`: 12000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 0.5833

**Formula**

```
  Ingestion Cost = log_ingestion_gb * skus.requests.unit_price_usd
  Total = ingestion_cost
```

**Cost contribution**

```
  Ingestion Cost         $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected log/metric ingestion SKU: monitoring_ondemand.; Assumed 10.0 GiB log/metric ingestion per month.

#### AZURE — Azure Monitor

**Monthly estimate:** $10.00 – $10.00

**Service selection**
- Architecture options: `['Azure Monitor']`
- Selected: **Azure Monitor**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | DZH318Z0BQLB/0DV0 | Alerts System Log Monitored at 10 Minute Frequency | $1.00000000 | 1/Month | 12000 | — | $12000.00 |

**SKU selection notes**

- Selected log/metric ingestion SKU: alerts.
- Assumed 10.0 GiB log/metric ingestion per month.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: production
- requests_per_user_per_month: 120
- request_share_for_component: 0.01
- avg_request_duration_seconds: 0.35
- cpu_vcpu: 0.5
- memory_gib: 1.0
- storage_per_user_gib: 0.5
- Derived usage variables:
  - `avg_request_duration`: 0.35
  - `cpu`: 0.5
  - `duration`: 4200
  - `egress`: 600
  - `egress_gb`: 600
  - `execution`: 2400
  - `log_ingestion_gb`: 10
  - `memory`: 1.1667
  - `memory_gib`: 1
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 200000
  - `monthly_executions`: 2400
  - `monthly_gb_seconds`: 4200
  - `monthly_memory_gib_hours`: 1.1667
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.5833
  - `requests`: 12000
  - `storage`: 5000
  - `storage_gib`: 5000
  - `vcpu`: 0.5833

**Formula**

```
  Ingestion Cost = log_ingestion_gb * skus.requests.unit_price_usd
  Total = ingestion_cost
```

**Cost contribution**

```
  Ingestion Cost         $     10.00
  Total                  $     10.00  (range $10.00–$10.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected log/metric ingestion SKU: alerts.; Assumed 10.0 GiB log/metric ingestion per month.

---

## Scenario: SocialFeed

_Mobile social feed, MVP, ~10,000 users, heavy media_

- Users: **10000** | Stage: **mvp**
- Requirements: `{'auth': True, 'file_upload': True, 'background_processing': True, 'ai': False, 'dashboards': False, 'payments': False}`

### Component: Mobile App (`mobile_app`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Amplify | $2.95–$3.99 | medium |
| GCP | Firebase | $0.00–$0.00 | low |
| AZURE | Azure App Center | $0.00–$0.00 | low |

- Nominal (low) cost spread across providers: $2.95/month (gcp=$0.00 vs aws=$2.95).
- Mapped equivalents: AWS=Amplify, GCP=Firebase, AZURE=Azure App Center. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs
  - AZURE: $0 — likely missing catalog or SKUs

#### AWS — Amplify

**Monthly estimate:** $2.95 – $3.99

**Service selection**
- Architecture options: `['Amplify']`
- Selected: **Amplify**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 2500 | — | $0.12 |
| requests | R782FWVAKEGNQS8S | USD 0.20 per GB-Hour for Amplify Hosting Compute | $0.00005556 | GB-Seconds | 60000 | — | $3.33 |

**SKU selection notes**

- Selected hosting storage SKU: requests.
- Selected hosting requests SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 4500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 1.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 4500
  - `monthly_memory_gib_hours`: 1.25
  - `monthly_requests`: 60000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.625
  - `requests`: 60000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.625

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      3.33
  Storage Cost           $      0.14
  Total                  $      2.95  (range $2.95–$3.99)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected hosting storage SKU: requests.; Selected hosting requests SKU: requests.

#### GCP — Firebase

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Firebase']`
- Selected: **Firebase**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No priced hosting storage SKU found in catalog.
- No priced hosting requests SKU found in catalog.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 4500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 1.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 4500
  - `monthly_memory_gib_hours`: 1.25
  - `monthly_requests`: 60000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.625
  - `requests`: 60000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.625

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced hosting storage SKU found in catalog.; No priced hosting requests SKU found in catalog.; no_priced_skus:mobile_app
- Fuzzy / fallback matching:
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.
  - No priced hosting storage SKU found in catalog.
  - No priced hosting requests SKU found in catalog.

#### AZURE — Azure App Center

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Azure App Center']`
- Selected: **Azure App Center**
- Catalog in Firestore: no
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.15
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 4500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 1.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 4500
  - `monthly_memory_gib_hours`: 1.25
  - `monthly_requests`: 60000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.625
  - `requests`: 60000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.625

**Formula**

```
N/A
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No Firestore pricing catalog document matched this service.
- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog document missing from Firestore.
- Selection / default notes: catalog:azure:Azure App Center

---

### Component: Media CDN (`cdn`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | CloudFront | $0.00–$0.00 | medium |
| GCP | Networking | $360.00–$360.00 | medium |
| AZURE | Content Delivery Network | $1293.00–$1293.00 | medium |

- Nominal (low) cost spread across providers: $1293.00/month (aws=$0.00 vs azure=$1293.00).
- Mapped equivalents: AWS=CloudFront, GCP=Networking, AZURE=Content Delivery Network. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — CloudFront

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['CloudFront']`
- Selected: **CloudFront**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | UH5MRG7QT9XX6YBP | $6.0E-7  per Request for  in US East (N. Virginia) | $0.00000060 | Request | 240 | — | $0.00 |

**SKU selection notes**

- Selected CDN egress SKU: requests.
- CDN egress assumed 3000.0 GiB/month for 10000 users.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.2
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 6000
  - `egress`: 240
  - `egress_gb`: 3000
  - `execution`: 30000
  - `memory`: 1.6667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 6000
  - `monthly_memory_gib_hours`: 1.6667
  - `monthly_requests`: 80000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.8333
  - `requests`: 80000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.8333

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: MEDIUM**

- Computed monthly cost is zero.
- Selection / default notes: Selected CDN egress SKU: requests.; CDN egress assumed 3000.0 GiB/month for 10000 users.

#### GCP — Networking

**Monthly estimate:** $360.00 – $360.00

**Service selection**
- Architecture options: `['Networking']`
- Selected: **Networking**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | 307A-FED8-5B99 | Networking Data Transfer inter region Intercontinental (Excl | $0.12000000 | GiBy | 240 | — | $360.00 |

**SKU selection notes**

- Selected CDN egress SKU: datatransfer_ondemand.
- CDN egress assumed 3000.0 GiB/month for 10000 users.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.2
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 6000
  - `egress`: 240
  - `egress_gb`: 3000
  - `execution`: 30000
  - `memory`: 1.6667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 6000
  - `monthly_memory_gib_hours`: 1.6667
  - `monthly_requests`: 80000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.8333
  - `requests`: 80000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.8333

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $    360.00
  Total                  $    360.00  (range $360.00–$360.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: datatransfer_ondemand.; CDN egress assumed 3000.0 GiB/month for 10000 users.

#### AZURE — Content Delivery Network

**Monthly estimate:** $1293.00 – $1293.00

**Service selection**
- Architecture options: `['Content Delivery Network']`
- Selected: **Content Delivery Network**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| egress | DZH318Z0BXV8/000V | Custom Acceleration 2 Data Transfer | $0.43100000 | 1 GB | 240 | — | $1293.00 |

**SKU selection notes**

- Selected CDN egress SKU: egress.
- CDN egress assumed 3000.0 GiB/month for 10000 users.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.2
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 6000
  - `egress`: 240
  - `egress_gb`: 3000
  - `execution`: 30000
  - `memory`: 1.6667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 6000
  - `monthly_memory_gib_hours`: 1.6667
  - `monthly_requests`: 80000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.8333
  - `requests`: 80000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.8333

**Formula**

```
  Egress Cost = egress_gb * skus.egress.unit_price_usd
  Total = egress_cost
```

**Cost contribution**

```
  Egress Cost            $   1293.00
  Total                  $   1293.00  (range $1293.00–$1293.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected CDN egress SKU: egress.; CDN egress assumed 3000.0 GiB/month for 10000 users.

---

### Component: API Gateway (`api_gateway`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | API Gateway | $0.00–$0.00 | low |
| GCP | API Gateway | $0.36–$0.48 | low |
| AZURE | API Management | $150.00–$150.00 | medium |

- Nominal (low) cost spread across providers: $150.00/month (aws=$0.00 vs azure=$150.00).
- Mapped equivalents: AWS=API Gateway, GCP=API Gateway, AZURE=API Management. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - AWS: fallback or weak catalog match
  - GCP: fallback or weak catalog match
  - GCP: unusually high requests cost ($420000) — verify SKU/unit

#### AWS — API Gateway

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | FC2TWT2UEPTBKVBX | $1/million requests - API Gateway HTTP API (first 300 millio | $0.00000100 | Requests | 140000 | — | $0.14 |

**SKU selection notes**

- No priced gateway capacity unit SKU found in catalog.
- Selected API calls SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 10500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 2.9167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 10500
  - `monthly_memory_gib_hours`: 2.9167
  - `monthly_requests`: 140000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.4583
  - `requests`: 140000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 1.4583

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced gateway capacity unit SKU found in catalog.; Selected API calls SKU: requests.
- Fuzzy / fallback matching:
  - No priced gateway capacity unit SKU found in catalog.
  - No priced gateway capacity unit SKU found in catalog.

#### GCP — API Gateway

**Monthly estimate:** $0.36 – $0.48

**Service selection**
- Architecture options: `['API Gateway']`
- Selected: **API Gateway**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | fallback-request-pricing | Fallback API call pricing | $3.00000000 | 1M requests | 140000 | — | $420000.00 |

**SKU selection notes**

- No priced gateway capacity unit SKU found in catalog.
- No priced API calls SKU found in catalog.
- No API call SKU in catalog; using fallback $3.00/million requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 10500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 2.9167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 10500
  - `monthly_memory_gib_hours`: 2.9167
  - `monthly_requests`: 140000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.4583
  - `requests`: 140000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 1.4583

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = request_cost
```

**Cost contribution**

```
  Request Cost           $      0.42
  Total                  $      0.36  (range $0.36–$0.48)
```

**Confidence: LOW**

- Fallback pricing was used because the catalog lacked a suitable SKU.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No priced gateway capacity unit SKU found in catalog.; No priced API calls SKU found in catalog.; No API call SKU in catalog; using fallback $3.00/million requests.
- Fuzzy / fallback matching:
  - No priced gateway capacity unit SKU found in catalog.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.
  - No priced gateway capacity unit SKU found in catalog.
  - No priced API calls SKU found in catalog.
  - No API call SKU in catalog; using fallback $3.00/million requests.

#### AZURE — API Management

**Monthly estimate:** $150.00 – $150.00

**Service selection**
- Architecture options: `['API Management']`
- Selected: **API Management**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | DZH318Z0BQCM/00QT | Basic v2 Secondary Unit | $0.20548000 | 1 Hour | 730 | — | $150.00 |

**SKU selection notes**

- Selected gateway capacity unit SKU: basic_v2.
- API gateway sized at 1 capacity unit(s).

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.35
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 10500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `gateway_units`: 1
  - `instance_billable_units`: 730
  - `memory`: 2.9167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 10500
  - `monthly_memory_gib_hours`: 2.9167
  - `monthly_requests`: 140000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.4583
  - `requests`: 140000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 1.4583

**Formula**

```
  Instance Cost = gateway_units * instance_billable_units * skus.instance.unit_price_usd
  Total = instance_cost
```

**Cost contribution**

```
  Instance Cost          $    150.00
  Total                  $    150.00  (range $150.00–$150.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected gateway capacity unit SKU: basic_v2.; API gateway sized at 1 capacity unit(s).

---

### Component: Feed API (`app_service`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Lambda | $0.02–$0.03 | medium |
| GCP | Cloud Run | $0.04–$0.06 | medium |
| AZURE | Functions | $0.34–$0.46 | medium |

- Nominal (low) cost spread across providers: $0.32/month (aws=$0.02 vs azure=$0.34).
- Mapped equivalents: AWS=Lambda, GCP=Cloud Run, AZURE=Functions. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Lambda

**Monthly estimate:** $0.02 – $0.03

**Service selection**
- Architecture options: `['Lambda']`
- Selected: **Lambda**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 120000 | — | $0.02 |
| execution | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 30000 | — | $0.01 |

**SKU selection notes**

- Selected requests SKU: requests.
- Selected gb-seconds SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 9000
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 2.5
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 9000
  - `monthly_memory_gib_hours`: 2.5
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.25
  - `requests`: 120000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 1.25

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $      0.02
  Duration Cost          $      0.00
  Total                  $      0.02  (range $0.02–$0.03)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected requests SKU: requests.; Selected gb-seconds SKU: requests.

#### GCP — Cloud Run

**Monthly estimate:** $0.04 – $0.06

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.25 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 2.5 | — | $0.04 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 120000 | — | $0.04 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 9000
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 2.5
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 9000
  - `monthly_memory_gib_hours`: 2.5
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.25
  - `requests`: 120000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 1.25

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.05
  Request Cost           $      0.00
  Total                  $      0.04  (range $0.04–$0.06)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Functions

**Monthly estimate:** $0.34 – $0.46

**Service selection**
- Architecture options: `['Functions']`
- Selected: **Functions**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| execution | DZH318Z0DW2R/00BL | Always Ready Baseline | $0.00000500 | 1 GB Second | 30000 | — | $0.13 |
| cpu | DZH318Z0BXVK/000L | Premium vCPU Duration | $0.17500000 | 1 Hour | 0.25 | — | $0.04 |
| memory | DZH318Z0BXVK/000J | Premium Memory Duration | $0.01300000 | 1 GiB Hour | 2.5 | — | $0.03 |

**SKU selection notes**

- Selected execution SKU: always_ready.
- Selected cpu SKU: cpu.
- Selected memory SKU: memory.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.3
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 9000
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 2.5
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 9000
  - `monthly_memory_gib_hours`: 2.5
  - `monthly_requests`: 120000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 1.25
  - `requests`: 120000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 1.25

**Formula**

```
  Execution Cost = monthly_executions * skus.execution.unit_price_usd
  Vcpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Total = execution_cost + vcpu_cost + memory_cost
```

**Cost contribution**

```
  Execution Cost         $      0.15
  Vcpu Cost              $      0.22
  Memory Cost            $      0.03
  Total                  $      0.34  (range $0.34–$0.46)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected execution SKU: always_ready.; Selected cpu SKU: cpu.; Selected memory SKU: memory.

---

### Component: Feed Cache (`cache`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | ElastiCache | $912.50–$912.50 | medium |
| GCP | Cloud Memorystore for Redis | $400.38–$400.38 | medium |
| AZURE | Redis Cache | $205.13–$205.13 | medium |

- Nominal (low) cost spread across providers: $707.37/month (azure=$205.13 vs aws=$912.50).
- Mapped equivalents: AWS=ElastiCache, GCP=Cloud Memorystore for Redis, AZURE=Redis Cache. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — ElastiCache

**Monthly estimate:** $912.50 – $912.50

**Service selection**
- Architecture options: `['ElastiCache']`
- Selected: **ElastiCache**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | TBRAD3QVTT9W9JEV | $1.25 per Hr for ExtendedSupportYr3-NodeUsage:cache.r6gd.xla | $1.25000000 | Hrs | 730 | — | $912.50 |

**SKU selection notes**

- Selected cache node SKU: use1_extendedsupportyr3_nodeusage_cache_r6gd_xlarge.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.03
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `instance_billable_units`: 730
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.125

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Total = instance_cost
```

**Cost contribution**

```
  Instance Cost          $    912.50
  Total                  $    912.50  (range $912.50–$912.50)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cache node SKU: use1_extendedsupportyr3_nodeusage_cache_r6gd_xlarge.

#### GCP — Cloud Memorystore for Redis

**Monthly estimate:** $400.38 – $400.38

**Service selection**
- Architecture options: `['Cloud Memorystore for Redis']`
- Selected: **Cloud Memorystore for Redis**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | 06E5-8CC1-F8A9 | Redis Cluster Node Highcpu Medium Toronto | $0.54846000 | h | 730 | — | $400.38 |

**SKU selection notes**

- Selected cache node SKU: cpu.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.03
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `instance_billable_units`: 730
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.125

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Total = instance_cost
```

**Cost contribution**

```
  Instance Cost          $    400.38
  Total                  $    400.38  (range $400.38–$400.38)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cache node SKU: cpu.

#### AZURE — Redis Cache

**Monthly estimate:** $205.13 – $205.13

**Service selection**
- Architecture options: `['Redis Cache']`
- Selected: **Redis Cache**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| instance | DZH318Z0BQH2/001D | C3 Cache Instance | $0.28100000 | 1 Hour | 730 | — | $205.13 |

**SKU selection notes**

- Selected cache node SKU: c3.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.03
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 900
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `instance_billable_units`: 730
  - `memory`: 0.25
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 900
  - `monthly_memory_gib_hours`: 0.25
  - `monthly_requests`: 12000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.125
  - `requests`: 12000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.125

**Formula**

```
  Instance Cost = instance_billable_units * skus.instance.unit_price_usd
  Total = instance_cost
```

**Cost contribution**

```
  Instance Cost          $    205.13
  Total                  $    205.13  (range $205.13–$205.13)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cache node SKU: c3.

---

### Component: User Data (`database`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | DynamoDB | $212.50–$287.50 | medium |
| GCP | Cloud Firestore | $0.00–$0.00 | low |
| AZURE | Azure Cosmos DB | $106.26–$143.76 | medium |

- Nominal (low) cost spread across providers: $212.50/month (gcp=$0.00 vs aws=$212.50).
- Mapped equivalents: AWS=DynamoDB, GCP=Cloud Firestore, AZURE=Azure Cosmos DB. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.
- **Potential issues to review:**
  - GCP: fallback or weak catalog match
  - GCP: $0 — likely missing catalog or SKUs

#### AWS — DynamoDB

**Monthly estimate:** $212.50 – $287.50

**Service selection**
- Architecture options: `['DynamoDB']`
- Selected: **DynamoDB**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | 4W4ZMC46EHE8XTTZ | $0.125 per million read request units (N. Virginia) | $0.00000012 | ReadRequestUnits | 20000 | — | $0.00 |
| storage | 3ADXMU9RYGKRUA9W | $0.10000 per GB of data exported in US East (N. Virginia) | $0.10000000 | GB | 2500 | — | $212.50 |

**SKU selection notes**

- Selected read/write requests SKU: requests.
- Selected storage SKU: use1_exportdatasize_bytes.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.4167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 1500
  - `monthly_memory_gib_hours`: 0.4167
  - `monthly_requests`: 20000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.2083
  - `requests`: 20000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.2083

**Formula**

```
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.00
  Storage Cost           $    250.00
  Total                  $    212.50  (range $212.50–$287.50)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected read/write requests SKU: requests.; Selected storage SKU: use1_exportdatasize_bytes.

#### GCP — Cloud Firestore

**Monthly estimate:** $0.00 – $0.00

**Service selection**
- Architecture options: `['Cloud Firestore']`
- Selected: **Cloud Firestore**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

_No SKUs matched._

**SKU selection notes**

- No read/write requests SKU found in catalog.
- No priced storage SKU found in catalog.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.4167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 1500
  - `monthly_memory_gib_hours`: 0.4167
  - `monthly_requests`: 20000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.2083
  - `requests`: 20000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.2083

**Formula**

```
  Total = 0
```

**Cost contribution**

```
  (no priced SKUs)
  Total                  $      0.00  (range $0.00–$0.00)
```

**Confidence: LOW**

- No SKUs were selected for pricing.
- Computed monthly cost is zero.
- Catalog matching did not find a confidently priced SKU for a required role.
- Selection / default notes: No read/write requests SKU found in catalog.; No priced storage SKU found in catalog.; no_priced_skus:database
- Fuzzy / fallback matching:
  - No priced storage SKU found in catalog.
  - No priced storage SKU found in catalog.

#### AZURE — Azure Cosmos DB

**Monthly estimate:** $106.26 – $143.76

**Service selection**
- Architecture options: `['Azure Cosmos DB']`
- Selected: **Azure Cosmos DB**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | DZH318Z0CDGF/0019 | Standard Read Operations | $0.00400000 | 10K | 20000 | — | $80.00 |
| storage | DZH318Z0CF60/0005 | 256 GiB Disk | $0.05000000 | 1/Hour | 2500 | — | $106.25 |

**SKU selection notes**

- Selected read/write requests SKU: standard.
- Selected storage SKU: memory.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.05
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 1500
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.4167
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 1500
  - `monthly_memory_gib_hours`: 0.4167
  - `monthly_requests`: 20000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.2083
  - `requests`: 20000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.2083

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.01
  Storage Cost           $    125.00
  Total                  $    106.26  (range $106.26–$143.76)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected read/write requests SKU: standard.; Selected storage SKU: memory.

---

### Component: Media Storage (`object_storage`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | S3 | $205.28–$277.73 | medium |
| GCP | Cloud Storage | $85.14–$115.18 | medium |
| AZURE | Blob Storage | $131.56–$178.00 | medium |

- Nominal (low) cost spread across providers: $120.14/month (gcp=$85.14 vs aws=$205.28).
- Mapped equivalents: AWS=S3, GCP=Cloud Storage, AZURE=Blob Storage. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — S3

**Monthly estimate:** $205.28 – $277.73

**Service selection**
- Architecture options: `['S3']`
- Selected: **S3**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 2500 | — | $48.88 |
| requests | D44ANS9DERJUGN3R | $0.023 per GB - first 50 TB / month prorated for objects del | $0.02300000 | GB-Mo | 8000 | — | $184.00 |

**SKU selection notes**

- Selected object storage SKU: earlydelete_int.
- Selected storage operations SKU: earlydelete_int.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 600
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.1667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 600
  - `monthly_memory_gib_hours`: 0.1667
  - `monthly_requests`: 8000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0833
  - `requests`: 8000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.0833

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $    184.00
  Storage Cost           $     57.50
  Total                  $    205.28  (range $205.28–$277.73)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: earlydelete_int.; Selected storage operations SKU: earlydelete_int.

#### GCP — Cloud Storage

**Monthly estimate:** $85.14 – $115.18

**Service selection**
- Architecture options: `['Cloud Storage']`
- Selected: **Cloud Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | 0A5B-5BB2-9A38 | Cloud CDN Cache Fill from Europe to Middle East | $0.04000000 | GiBy | 2500 | — | $85.00 |
| requests | 007A-40B7-63BC | Multi-Region Durable Reduced Availability Class A Operations | $0.00002000 | count | 8000 | — | $0.16 |

**SKU selection notes**

- Selected object storage SKU: cdncachefill_ondemand.
- Selected storage operations SKU: draops_ondemand.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 600
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.1667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 600
  - `monthly_memory_gib_hours`: 0.1667
  - `monthly_requests`: 8000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0833
  - `requests`: 8000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.0833

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.16
  Storage Cost           $    100.00
  Total                  $     85.14  (range $85.14–$115.18)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: cdncachefill_ondemand.; Selected storage operations SKU: draops_ondemand.

#### AZURE — Blob Storage

**Monthly estimate:** $131.56 – $178.00

**Service selection**
- Architecture options: `['Blob Storage']`
- Selected: **Blob Storage**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| storage | DZH318Z0BNWT/00CD | ZRS Data Stored | $0.06190000 | 1 GB/Month | 2500 | — | $131.54 |
| requests | DZH318Z0CBTJ/05R9 | Smart Tier GRS Monitoring Operations | $0.04000000 | 10K | 8000 | — | $320.00 |

**SKU selection notes**

- Selected object storage SKU: storage.
- Selected storage operations SKU: smart_tier_grs.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.02
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 600
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.1667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 600
  - `monthly_memory_gib_hours`: 0.1667
  - `monthly_requests`: 8000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.0833
  - `requests`: 8000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.0833

**Formula**

```
  Request Cost = (monthly_requests / 10000) * skus.requests.unit_price_usd
  Storage Cost = storage_gib * skus.storage.unit_price_usd
  Total = request_cost + storage_cost
```

**Cost contribution**

```
  Request Cost           $      0.03
  Storage Cost           $    154.75
  Total                  $    131.56  (range $131.56–$178.00)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected object storage SKU: storage.; Selected storage operations SKU: smart_tier_grs.

---

### Component: Media Processor (`queue_worker`)

**Cross-provider comparison**

| Provider | Service | Monthly (low–high) | Confidence |
|----------|---------|-------------------|------------|
| AWS | Lambda | $0.01–$0.01 | medium |
| GCP | Cloud Run | $0.01–$0.02 | medium |
| AZURE | Functions | $0.18–$0.25 | medium |

- Nominal (low) cost spread across providers: $0.17/month (aws=$0.01 vs azure=$0.18).
- Mapped equivalents: AWS=Lambda, GCP=Cloud Run, AZURE=Functions. Differences reflect catalog coverage, SKU selection rules, and unit semantics—not live billing.

#### AWS — Lambda

**Monthly estimate:** $0.01 – $0.01

**Service selection**
- Architecture options: `['Lambda']`
- Selected: **Lambda**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| requests | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 32000 | — | $0.01 |
| execution | GU2ZS9HVP6QTQ7KE | AWS Lambda - Total Requests - US East (Northern Virginia) | $0.00000020 | Requests | 30000 | — | $0.01 |

**SKU selection notes**

- Selected requests SKU: requests.
- Selected gb-seconds SKU: requests.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 2400
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.6667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 2400
  - `monthly_memory_gib_hours`: 0.6667
  - `monthly_requests`: 32000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.3333
  - `requests`: 32000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.3333

**Formula**

```
  Request Cost = monthly_requests * skus.requests.unit_price_usd
  Duration Cost = monthly_gb_seconds * skus.execution.unit_price_usd
  Total = request_cost + duration_cost
```

**Cost contribution**

```
  Request Cost           $      0.01
  Duration Cost          $      0.00
  Total                  $      0.01  (range $0.01–$0.01)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected requests SKU: requests.; Selected gb-seconds SKU: requests.

#### GCP — Cloud Run

**Monthly estimate:** $0.01 – $0.02

**Service selection**
- Architecture options: `['Cloud Run']`
- Selected: **Cloud Run**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| cpu | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 0.25 | — | $0.00 |
| memory | 1EA7-1C33-8290 | Cloud Run Network Data Transfer Out via Carrier Peering Netw | $0.02000000 | GiBy | 0.6667 | — | $0.01 |
| requests | 009A-0268-0ACE | Instances CPU in me-central1 | $0.00000032 | s | 32000 | — | $0.01 |

**SKU selection notes**

- Selected cpu SKU: cpu.
- Selected memory SKU: peeringorinterconnectegress_ondemand.
- Selected requests SKU: cpu.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 2400
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.6667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 2400
  - `monthly_memory_gib_hours`: 0.6667
  - `monthly_requests`: 32000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.3333
  - `requests`: 32000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.3333

**Formula**

```
  Cpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Request Cost = (monthly_requests / 1000000) * skus.requests.unit_price_usd
  Total = cpu_cost + memory_cost + request_cost
```

**Cost contribution**

```
  Cpu Cost               $      0.00
  Memory Cost            $      0.01
  Request Cost           $      0.00
  Total                  $      0.01  (range $0.01–$0.02)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected cpu SKU: cpu.; Selected memory SKU: peeringorinterconnectegress_ondemand.; Selected requests SKU: cpu.

#### AZURE — Functions

**Monthly estimate:** $0.18 – $0.25

**Service selection**
- Architecture options: `['Functions']`
- Selected: **Functions**
- Catalog in Firestore: yes
- Rule: The architecture maps one primary cloud service per provider. The estimator uses the first non-skipped option from that list.

**Selected SKUs**

| Role | SKU ID | Name | Unit price | Usage unit | Quantity | Free tier | Cost |
|------|--------|------|------------|------------|----------|-----------|------|
| execution | DZH318Z0DW2R/00BL | Always Ready Baseline | $0.00000500 | 1 GB Second | 30000 | — | $0.13 |
| cpu | DZH318Z0BXVK/000L | Premium vCPU Duration | $0.17500000 | 1 Hour | 0.25 | — | $0.04 |
| memory | DZH318Z0BXVK/000J | Premium Memory Duration | $0.01300000 | 1 GiB Hour | 0.6667 | — | $0.01 |

**SKU selection notes**

- Selected execution SKU: always_ready.
- Selected cpu SKU: cpu.
- Selected memory SKU: memory.

**Usage assumptions**

- expected_users: 10000
- user_count: 10000
- stage: mvp
- requests_per_user_per_month: 40
- request_share_for_component: 0.08
- avg_request_duration_seconds: 0.15
- cpu_vcpu: 0.25
- memory_gib: 0.5
- storage_per_user_gib: 0.25
- Derived usage variables:
  - `avg_request_duration`: 0.15
  - `cpu`: 0.25
  - `duration`: 2400
  - `egress`: 240
  - `egress_gb`: 240
  - `execution`: 30000
  - `memory`: 0.6667
  - `memory_gib`: 0.5
  - `monthly_ai_requests`: 0
  - `monthly_auth_events`: 80000
  - `monthly_executions`: 30000
  - `monthly_gb_seconds`: 2400
  - `monthly_memory_gib_hours`: 0.6667
  - `monthly_requests`: 32000
  - `monthly_tokens`: 0
  - `monthly_vcpu_hours`: 0.3333
  - `requests`: 32000
  - `storage`: 2500
  - `storage_gib`: 2500
  - `vcpu`: 0.3333

**Formula**

```
  Execution Cost = monthly_executions * skus.execution.unit_price_usd
  Vcpu Cost = monthly_vcpu_hours * skus.cpu.unit_price_usd
  Memory Cost = monthly_memory_gib_hours * skus.memory.unit_price_usd
  Total = execution_cost + vcpu_cost + memory_cost
```

**Cost contribution**

```
  Execution Cost         $      0.15
  Vcpu Cost              $      0.06
  Memory Cost            $      0.01
  Total                  $      0.18  (range $0.18–$0.25)
```

**Confidence: MEDIUM**

- Selection / default notes: Selected execution SKU: always_ready.; Selected cpu SKU: cpu.; Selected memory SKU: memory.

---
