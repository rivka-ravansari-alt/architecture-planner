from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./architecture_planner.db"
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    app_name: str = "Archsari API"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    use_static_ai_response: bool = False  # set USE_STATIC_AI_RESPONSE=true in .env for local dev
    ai_prompts_dir: str = "./data/generation_prompts"
    ai_outputs_dir: str = "./data/generation_outputs"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
