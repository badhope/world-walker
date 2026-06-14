"""
Regional Industrial Economic Analysis Platform - unified configuration.

All defaults can be overridden via environment variables or a `.env` file.
"""

import json
import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # Basic metadata
    PROJECT_NAME: str = "Urban Pulse"
    PROJECT_NAME_ZH: str = "城市脉搏 — 城市经济智能分析"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment (dev / staging / production / test)
    APP_ENV: Literal["dev", "staging", "production", "test"] = "dev"

    # API service
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = "sqlite:///./data/regional_economic.db"

    # CORS
    # 0.0.0.0 不应出现在白名单 — 它是绑定地址,不是 Origin 头合法值
    CORS_ORIGINS: list[str] = json.loads(
        os.getenv(
            "CORS_ORIGINS",
            '["http://localhost:5173","http://localhost:8000","http://localhost:8080","http://127.0.0.1:8000","http://127.0.0.1:8080"]',
        )
    )

    # Scraper configuration
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_DELAY: float = 1.0

    # Cache
    CACHE_TTL: int = 3600
    CACHE_DIR: str = "./data/cache"

    # Data directories
    DATA_DIR: str = "./data"
    EXPORT_DIR: str = "./data/exports"
    RAW_DATA_DIR: str = "./data/raw"
    PROCESSED_DATA_DIR: str = "./data/processed"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str | None = None

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Analysis parameters
    DEFAULT_YEAR: int = 2025
    DEFAULT_REGION: str = "深圳"
    DEFAULT_INDUSTRY: str = "半导体"

    # GitHub / repository metadata
    REPO_URL: str = "https://github.com/badhope/national_stats"
    LICENSE: str = "GPL-3.0-or-later"

    model_config = {"case_sensitive": True, "env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _enforce_secret_key_in_production(self):
        """在 production 环境下强制要求显式 SECRET_KEY,避免使用开发默认值。"""
        if self.APP_ENV == "production" and self.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY must be explicitly set in production. "
                "Export the SECRET_KEY environment variable to a strong random value."
            )
        return self


def setup_logging(settings: Settings):
    """Configure the application-wide logging system."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if settings.LOG_FILE:
        handlers.append(logging.FileHandler(settings.LOG_FILE, encoding="utf-8"))

    logging.basicConfig(level=log_level, format=settings.LOG_FORMAT, handlers=handlers)


settings = Settings()
setup_logging(settings)

if settings.SECRET_KEY == "dev-secret-key-change-in-production":
    import warnings

    warnings.warn(
        "SECRET_KEY is using the default development value. Set the SECRET_KEY environment variable for production.",
        RuntimeWarning,
    )

if settings.ALGORITHM == "RS256" and not settings.SECRET_KEY.startswith("-----BEGIN"):
    import warnings

    warnings.warn(
        "SECRET_KEY does not appear to be an RSA private key. For RS256, a valid RSA key pair is required.",
        RuntimeWarning,
    )

Path("data").mkdir(parents=True, exist_ok=True)

