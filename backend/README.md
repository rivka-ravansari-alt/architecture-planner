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
├── clients/                # External APIs (OpenAI, Google OAuth)
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
3. Save prompt artifact
4. Call AI (`BaseAIClient` via factory)
5. Validate JSON (`AIResponseValidator`)
6. Save output artifact
7. Map to domain objects (`ComponentMapperService`)
8. Estimate costs (`CostEstimatorService`)
9. Persist to database (`ProjectRepository`)

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
