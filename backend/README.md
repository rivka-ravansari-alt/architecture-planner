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
| **params** | Shared constants | `VALID_COMPONENT_TYPES`, cost bands |

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
| `GCS_PROJECT_ID` | Optional; defaults to Application Default Credentials project |
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
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
cd backend
pytest
```
