"""Environment-backed application settings (secrets and deployment config)."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./architecture_planner.db"
    cors_allow_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    app_name: str = "Archsari API"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_request_timeout_seconds: float = 600.0
    openai_max_output_tokens: int = 8000
    use_static_ai_response: bool = False

    object_storage_provider: str = "gcs"
    object_storage_local_root: str = "./object-storage"
    object_storage_bucket: str = "archsari-generations-prod"
    gcs_project_id: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5173/api/auth/google/callback"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 10080
    frontend_url: str = "http://localhost:5173"
    session_cookie_name: str = "auth_session"
    session_cookie_secure: bool = False

    @field_validator("openai_api_key", "jwt_secret", "google_client_secret", mode="before")
    @classmethod
    def strip_secret_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()
