# Archsari

**Architecture Before Code** — plan application architecture before development. The tool is technology-agnostic:
components, cloud options, cost estimates, risks, and next steps — not languages or frameworks.

Architecture content is **AI-generated** from wizard inputs. **Cost estimates** and **cloud mapping** use fixed rules. Set `OPENAI_API_KEY` in `backend/.env` (see `.env.example`).

## Tech Stack

- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL (production) or SQLite (local dev)
- Frontend: React + Vite

## How It Works

1. User completes a 4-step wizard (project details, requirements).
2. On generate: build prompt → call AI → validate JSON → persist document.
3. Map components to AWS / GCP / Azure; estimate costs from component keys.
4. Show results; user can move components between Required and Optional (costs update client-side).

## Project Structure

```
backend/
  app/
    api/projects.py
    project_types.py       # wizard project type list
    rules/
      cloud_mapping.py     # component key → cloud services
      cost_estimator.py    # monthly cost ranges
    services/
      generation.py        # AI orchestration
      prompt_builder.py, ai_client.py, ai_validator.py, component_mapper.py
    models.py, schemas.py, database.py, config.py, main.py
  tests/
frontend/
  src/components/          # wizard steps
  src/recompute.js         # client-side cost split
```

## Running Locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000 (docs at `/docs`)

Tests (mocked AI, no API key):

```bash
.venv\Scripts\python -m pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 (proxies `/api` to port 8000)

## Docker (local)

Copy `backend/.env.example` to `backend/.env` and set secrets. OAuth redirect for local Docker:

- `FRONTEND_URL=http://localhost:8080`
- `GOOGLE_REDIRECT_URI=http://localhost:8080/api/auth/google/callback`

```bash
docker compose up --build
```

App: http://localhost:8080 · API (direct): http://localhost:8000

## Google Cloud Run (production)

Two services — **API** (`backend/Dockerfile`) and **web** (`frontend/Dockerfile`). The web service is the public URL; it proxies `/api` to the API so login cookies stay same-origin.

```
Browser → archsari-web (Cloud Run, port $PORT)
            ├─ /        → React static files
            └─ /api/*   → archsari-api (BACKEND_URL)
```

### 1. One-time GCP setup

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com

gcloud artifacts repositories create archsari --repository-format=docker --location=us-central1
```

Create **Cloud SQL** (PostgreSQL), store secrets in **Secret Manager** (`openai-api-key`, `jwt-secret`, `google-client-secret`), and a **Google OAuth** Web client. See `deploy/gcp.env.example` for env var names.

### 2. Deploy API

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/archsari/archsari-api:latest ./backend

gcloud run deploy archsari-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/archsari/archsari-api:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --timeout 300 \
  --memory 512Mi \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest,JWT_SECRET=jwt-secret:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest \
  --set-env-vars "DATABASE_URL=postgresql+psycopg://USER:PASS@/architecture_planner?host=/cloudsql/PROJECT:REGION:INSTANCE,SESSION_COOKIE_SECURE=true,GOOGLE_CLIENT_ID=xxx,CORS_ALLOW_ORIGINS=https://placeholder,FRONTEND_URL=https://placeholder,GOOGLE_REDIRECT_URI=https://placeholder/api/auth/google/callback"
```

Note the API URL from deploy output (e.g. `https://archsari-api-xxxxx.run.app`).

### 3. Deploy web

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/archsari/archsari-web:latest ./frontend

gcloud run deploy archsari-web \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/archsari/archsari-web:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "BACKEND_URL=https://archsari-api-xxxxx.run.app"
```

### 4. Point OAuth at the web URL

Use the **web** service URL everywhere users browse:

- Google Console redirect: `https://archsari-web-xxxxx.run.app/api/auth/google/callback`
- Update API env: `FRONTEND_URL`, `GOOGLE_REDIRECT_URI`, `CORS_ALLOW_ORIGINS` to that URL

```bash
gcloud run services update archsari-api --region us-central1 \
  --update-env-vars "FRONTEND_URL=https://archsari-web-xxxxx.run.app,GOOGLE_REDIRECT_URI=https://archsari-web-xxxxx.run.app/api/auth/google/callback,CORS_ALLOW_ORIGINS=https://archsari-web-xxxxx.run.app"
```

### CI/CD

`cloudbuild.yaml` builds and deploys both services. Set substitution `_BACKEND_URL` to your API URL before the web deploy step runs:

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_BACKEND_URL=https://archsari-api-xxxxx.run.app
```

## API Endpoints

- `GET /api/project-types`
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{id}`
- `POST /api/projects/{id}/generate`

## Cost Estimates

Rough ranges from static configuration (user tier, stage, feature flags). Not live billing data.
