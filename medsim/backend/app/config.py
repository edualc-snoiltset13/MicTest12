"""Runtime configuration for the MedSimQA backend.

Everything is read from the environment (12-factor) with safe local defaults so
that ``uvicorn app.main:app`` works on a fresh checkout with zero setup.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings.

    Attributes are populated from environment variables prefixed with
    ``MEDSIM_`` (e.g. ``MEDSIM_DATABASE_URL``).
    """

    model_config = SettingsConfigDict(
        env_prefix="MEDSIM_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- service identity --------------------------------------------------
    app_name: str = "MedSimQA API"
    app_version: str = "1.0.0"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # --- transport ---------------------------------------------------------
    host: str = "0.0.0.0"  # noqa: S104 - container binds all interfaces on purpose
    port: int = 8000
    root_path: str = ""
    api_prefix: str = "/api/v1"

    # --- persistence -------------------------------------------------------
    # SQLite by default. Point at PostgreSQL in staging/production, e.g.
    #   MEDSIM_DATABASE_URL=postgresql+psycopg://medsim:secret@db:5432/medsim
    database_url: str = f"sqlite:///{BASE_DIR / 'medsim.db'}"
    sql_echo: bool = False

    # --- seeding -----------------------------------------------------------
    data_dir: Path = DATA_DIR
    auto_seed: bool = True
    reseed_on_boot: bool = False

    # --- security ----------------------------------------------------------
    # NOTE: the default is intentionally obviously-not-a-secret. The deploy
    # script generates a real one and the app refuses to boot with the default
    # when environment == "production" (see validate_production()).
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 60 * 60 * 8
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"

    # --- QA affordances ----------------------------------------------------
    # The QA suite (Phase 3) drives these to simulate hostile networks without
    # needing a real proxy in CI. They are hard-disabled in production.
    chaos_enabled: bool = False
    chaos_latency_ms: int = 0
    chaos_error_rate: float = 0.0
    chaos_malformed_rate: float = 0.0

    # --- observability -----------------------------------------------------
    log_level: str = "INFO"
    log_json: bool = False
    request_id_header: str = "X-Request-ID"

    @field_validator("chaos_error_rate", "chaos_malformed_rate")
    @classmethod
    def _rate_in_unit_interval(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("chaos rates must be between 0.0 and 1.0")
        return value

    @field_validator("log_level")
    @classmethod
    def _valid_log_level(cls, value: str) -> str:
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return upper

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def validate_production(self) -> None:
        """Fail fast on insecure production configuration."""
        if not self.is_production:
            return
        problems: list[str] = []
        if self.jwt_secret == "dev-only-insecure-secret-change-me":
            problems.append("MEDSIM_JWT_SECRET is still the development default")
        if self.debug:
            problems.append("MEDSIM_DEBUG must be false in production")
        if self.chaos_enabled:
            problems.append("MEDSIM_CHAOS_ENABLED must be false in production")
        if "*" in self.cors_origin_list:
            problems.append("wildcard CORS origin is not permitted in production")
        if problems:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor used as a FastAPI dependency."""
    settings = Settings()
    settings.validate_production()
    return settings


def reset_settings_cache() -> None:
    """Clear the settings cache. Used by the test-suite between fixtures."""
    get_settings.cache_clear()
    os.environ.pop("MEDSIM_SETTINGS_CACHE_BUSTER", None)
