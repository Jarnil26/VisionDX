"""
VisionDX — Application Configuration
Uses pydantic-settings to load from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "VisionDX"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-long-random-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./visiondx.db"
    database_url_sync: str = "sqlite:///./visiondx.db"

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── File Storage ─────────────────────────────────────────────────────────
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 20

    # ── Tesseract ────────────────────────────────────────────────────────────
    tesseract_cmd: str = "/usr/bin/tesseract"



    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # ── ML Model ─────────────────────────────────────────────────────────────
    model_path: str = "visiondx/ml/models/disease_predictor.pkl"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
