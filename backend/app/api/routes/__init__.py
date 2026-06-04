from app.api.routes.auth_routes import router as auth_router
from app.api.routes.health_routes import router as health_router
from app.api.routes.project_routes import router as project_router

__all__ = ["auth_router", "health_router", "project_router"]
