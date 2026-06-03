from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.projects import router as projects_router
from .config import settings
from .database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.use_static_ai_response:
        logger.warning("AI generation uses static JSON (USE_STATIC_AI_RESPONSE=true).")
    elif settings.openai_api_key:
        logger.info("AI generation uses OpenAI model %s.", settings.openai_model)
    else:
        logger.warning("OpenAI API key is not configured; /generate will fail.")
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "use_static_ai_response": settings.use_static_ai_response,
        "openai_configured": bool(settings.openai_api_key),
    }
