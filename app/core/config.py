import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    database_url: str
    llm_provider: str
    llm_model: str
    llm_api_key: str
    llm_base_url: str
    llm_enabled: bool
    llm_timeout_seconds: int
    ui_api_base_url: str


@lru_cache()
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AI Automation Agent"),
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        database_url=os.getenv("APP_DATABASE_URL", f"sqlite:///{(BASE_DIR / 'agent.db').as_posix()}"),
        llm_provider=os.getenv("APP_LLM_PROVIDER", "mock"),
        llm_model=os.getenv("APP_LLM_MODEL", "local-heuristic"),
        llm_api_key=os.getenv("APP_LLM_API_KEY", ""),
        llm_base_url=os.getenv("APP_LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_enabled=os.getenv("APP_LLM_ENABLED", "false").lower() == "true",
        llm_timeout_seconds=int(os.getenv("APP_LLM_TIMEOUT_SECONDS", "20")),
        ui_api_base_url=os.getenv("UI_API_BASE_URL", "http://127.0.0.1:8000"),
    )
