from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Placement Co-pilot API"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = f"sqlite:///{(BASE_DIR / 'placement.db').as_posix()}"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    session_cookie_name: str = "pc_session"
    session_header_name: str = "X-Session-Id"
    session_max_age_seconds: int = 60 * 60 * 24 * 30

    max_upload_bytes: int = 8 * 1024 * 1024
    max_resume_chars: int = 200_000
    pdf_magic_bytes: str = "%PDF-"

    jobs_provider: Literal["auto", "live", "mock"] = "auto"
    jobs_api_url: str = "https://jobicy.com/api/v2/remote-jobs"
    jobs_api_timeout_seconds: float = 12.0
    jobs_cache_ttl_seconds: int = 3600
    jobs_fetch_count: int = 50
    jobs_max_results: int = 12

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    rate_limit_upload_requests: int = 12

    llm_provider: Literal["auto", "ollama", "disabled"] = "auto"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    llm_timeout_seconds: float = 90.0
    llm_max_tokens: int = 600
    llm_context_tokens: int = 8192
    llm_temperature: float = 0.2

    @field_validator("database_url", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, value: str) -> str:
        prefix = "sqlite:///"
        if not value.startswith(prefix) or value == "sqlite:///:memory:":
            return value
        raw = value[len(prefix) :]
        if raw.startswith("/"):
            return value
        path = Path(raw)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return f"sqlite:///{path.as_posix()}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider != "disabled"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
