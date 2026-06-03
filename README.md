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

## API Endpoints

- `GET /api/project-types`
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{id}`
- `POST /api/projects/{id}/generate`

## Cost Estimates

Rough ranges from static configuration (user tier, stage, feature flags). Not live billing data.
