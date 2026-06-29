# Backend — Archsari API

FastAPI backend for the architecture planning wizard.

## Folder structure

```
app/
├── main.py                 # App factory, middleware, exception handlers
├── config/
│   ├── settings.py         # Secrets and env vars (DATABASE_URL, API keys)
│   └── params.py           # Non-secret constants (limits, catalogs, defaults)
├── core/
│   ├── database.py         # SQLAlchemy engine, sessions, schema init
│   ├── dependencies.py     # FastAPI DI (db, auth, services, AI client)
│   ├── exceptions.py       # Domain exception hierarchy
│   └── logging.py          # Structured log helpers
├── models/                 # SQLAlchemy ORM entities
├── schemas/                # Pydantic DTOs (request/response validation)
├── repositories/           # Database access (CRUD, queries)
├── services/               # Business logic orchestration
├── clients/                # External APIs (OpenAI, Google OAuth, object storage)
├── validators/             # Input/output validation (AI JSON schema)
├── utils/                  # Pure helpers (JWT, token estimate)
└── api/
    ├── controllers/        # HTTP adapters — call services, return DTOs
    └── routes/             # FastAPI route definitions (thin wiring)
```

## Layer responsibilities

| Layer | Responsibility | Example |
|-------|----------------|---------|
| **routes** | Wire HTTP methods to controllers | `auth_routes.py` |
| **controllers** | Parse validated input, invoke services | `ProjectController.generate_project` |
| **services** | Business rules and orchestration | `GenerationService.generate` |
| **repositories** | SQLAlchemy CRUD only | `ProjectRepository.persist_architecture` |
| **clients** | Third-party API calls | `OpenAIClient.generate` |
| **validators** | Structural validation | `AIResponseValidator.validate` |
| **schemas** | Request/response shapes | `ProjectCreate`, `ProjectDetail` |
| **models** | Database tables | `Project`, `User` |
| **params** | Shared constants | `COMPONENT_CATEGORY_*`, cost bands |

## Generation pipeline

`GenerationService` orchestrates these steps (each is a private method ≤40 lines):

1. Create audit request row
2. Build prompt (`PromptBuilderService`)
3. Save `request.json` to object storage (`GenerationStorageService`)
4. Call AI (`BaseAIClient` via factory)
5. Validate JSON (`AIResponseValidator`)
6. Save `response.json` to object storage (including failures after the AI call)
7. Map to domain objects (`ComponentMapperService`)
8. Estimate costs (`CostEstimatorService`)
9. Persist to database (`ProjectRepository`)

### Generation object storage

Every `/generate` run writes two JSON files under object storage:

```
gs://{OBJECT_STORAGE_BUCKET}/
  generations/          # GENERATION_STORAGE_PREFIX in params.py
    {generation_id}/
      request.json
      response.json
```

| File | Contents |
|------|----------|
| `request.json` | Project/user ids, project types, generation type, original wizard input, prompt sent to the model, model name, parameters, timestamp |
| `response.json` | Raw AI text, parsed JSON (if validation ran), validation result, errors (on failure), duration, timestamp |

Configure via `.env`:

| Variable | Purpose |
|----------|---------|
| `OBJECT_STORAGE_PROVIDER` | Default `gcs` — use Google Cloud Storage |
| `OBJECT_STORAGE_BUCKET` | GCS bucket name (e.g. `archsari-generations-prod`) |
| `GCS_PROJECT_ID` | Optional; GCP project for GCS and Firestore (defaults to ADC project) |
| `OBJECT_STORAGE_LOCAL_ROOT` | Only if `OBJECT_STORAGE_PROVIDER=local` (offline dev) |

`StorageClientFactory` uses **GCS** by default. **S3** is still a stub.

The `architecture_generation_requests` table stores `gs://...` URIs in `input_os_path` and `output_os_path`.

### GCS setup

**Local dev** (writes to the same bucket as production):

```bash
gcloud auth application-default login
```

Set in `backend/.env`:

```env
OBJECT_STORAGE_PROVIDER=gcs
OBJECT_STORAGE_BUCKET=archsari-generations-prod
GCS_PROJECT_ID=your-gcp-project-id
```

**Cloud Run** (same env vars; ADC from the service account — no key file needed):

1. **Create a bucket** (once per environment):

   ```bash
   gcloud storage buckets create gs://archsari-generations-prod \
     --project=YOUR_PROJECT_ID \
     --location=us-central1 \
     --uniform-bucket-level-access
   ```

2. **Grant the Cloud Run service account** write access:

   ```bash
   gcloud storage buckets add-iam-policy-binding gs://archsari-generations-prod \
     --member="serviceAccount:YOUR_CLOUD_RUN_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.objectAdmin"
   ```

3. **Set env vars** on the backend service (local `.env` or Cloud Run):

   - `OBJECT_STORAGE_PROVIDER=gcs` (default)
   - `OBJECT_STORAGE_BUCKET=archsari-generations-prod`
   - `GCS_PROJECT_ID=YOUR_PROJECT_ID` (optional if ADC project is correct)

4. **Redeploy** the backend image after changing env vars.

Objects appear at:

`gs://archsari-generations-prod/generations/{generation_id}/request.json`

To work offline without GCS, set `OBJECT_STORAGE_PROVIDER=local` and `OBJECT_STORAGE_LOCAL_ROOT=./object-storage`.

## Running locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --reload-dir app --port 8000
```

## Authentication performance

Google OAuth uses a single shared `GoogleOAuthClient` for the app process. OIDC discovery
metadata (`accounts.google.com/.well-known/openid-configuration`) is fetched once at
startup when OAuth is configured, then reused for `/auth/google` and
`/auth/google/callback`.

On **Google Cloud Run**, login still hits the API several times per sign-in. With
`min-instances=0` (default in `cloudbuild.yaml`), the first request after idle incurs a
cold start before OAuth or `/auth/me` can respond. Set `--min-instances=1` on the API
service to keep one container warm and reduce first-login latency.

## GCP pricing ingestion (Firestore)

Pricing sync reads enabled GCP service names from Firestore `gcp_catalog`,
matches them to the Google Cloud Billing Catalog by exact display name, fetches SKUs only for
those services, and upserts pricing documents back into Firestore. It does **not** sync the full
Google catalog.

Run sync via the Cloud Run Job entrypoint (see below) or locally:

```bash
cd backend
python -m app.jobs.pricing_sync_job --provider gcp
```

Register service names first (names only, exact billing display names):

```bash
cd backend
python scripts/seed_gcp_catalog_registry.py
```

Collections:
- `gcp_catalog` — enabled service registry and pricing docs (`id`, `name`, `skus`, `formula`)
- `price_import_runs` — sync audit log only (not used for price calculation)

Authentication uses **Application Default Credentials** (no API key):

| Environment | Setup |
|-------------|-------|
| **Local** | `gcloud auth application-default login` — enable Cloud Billing API + Firestore API |
| **Cloud Run** | Service account ADC; grant Firestore access (`roles/datastore.user`) |

Env vars: `GCS_PROJECT_ID`, `FIRESTORE_DATABASE` (default `(default)`), `GCP_BILLING_BASE_URL`.

### Cloud Run Job (automated sync)

Scheduled pricing sync runs as a **Cloud Run Job**. The job reuses the same backend image and calls `PricingSyncOrchestrator` directly:

```bash
cd backend
python -m app.jobs.pricing_sync_job --provider all
```

Provider choices: `gcp`, `aws`, `azure`, or `all`. You can also set `PRICING_SYNC_PROVIDER` instead of `--provider`.

**Deploy** (also wired in `cloudbuild.yaml` as `archsari-pricing-sync`):

```bash
gcloud run jobs deploy archsari-pricing-sync \
  --image=REGION-docker.pkg.dev/PROJECT/REPO/archsari-api:TAG \
  --region=REGION \
  --command=python,-m,app.jobs.pricing_sync_job \
  --args=--provider,all \
  --memory=1Gi \
  --task-timeout=3600 \
  --set-env-vars=GCS_PROJECT_ID=PROJECT,DATABASE_URL=...
```

Grant the job service account Firestore access (`roles/datastore.user`), Cloud Billing API access, and database connectivity (same as the API for AWS/Azure loaders).

**Cloud Scheduler** triggers the job (IAM auth — no shared secret on the API):

```bash
gcloud scheduler jobs create http pricing-sync-daily \
  --location=REGION \
  --schedule="0 3 * * *" \
  --uri="https://run.googleapis.com/v2/projects/PROJECT/locations/REGION/jobs/archsari-pricing-sync:run" \
  --http-method=POST \
  --oauth-service-account-email=scheduler-sa@PROJECT.iam.gserviceaccount.com \
  --oauth-token-scope=https://www.googleapis.com/auth/cloud-platform \
  --message-body='{"overrides":{"containerOverrides":[{"args":["--provider","all"]}]}}'
```

Grant the scheduler service account `roles/run.developer` (or `roles/run.jobsExecutor`) on the project.

## Tests

```bash
cd backend
pytest
```
