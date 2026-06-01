"""
国家经济数据分析平台 - 统一配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import json
import os
import logging


class Settings(BaseSettings):
    """应用配置"""
    # 基础信息
    PROJECT_NAME: str = "区域产业经济分析平台"
    VERSION: str = "4.0.0"
    API_V1_STR: str = "/api/v1"
    
    # API服务
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./data/national_stats.db"
    
    # CORS
    CORS_ORIGINS: List[str] = json.loads(os.getenv(
        "CORS_ORIGINS",
        '["http://localhost:5173","http://localhost:8000","http://localhost:8001","http://localhost:8080","http://127.0.0.1:8000","http://127.0.0.1:8001","http://127.0.0.1:8080","http://0.0.0.0:8000","http://0.0.0.0:8001"]'
    ))
    
    # 爬虫配置
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_DELAY: float = 1.0
    
    # 缓存
    CACHE_TTL: int = 3600
    CACHE_DIR: str = "./data/cache"
    
    # 数据目录
    DATA_DIR: str = "./data"
    EXPORT_DIR: str = "./data/exports"
    RAW_DATA_DIR: str = "./data/raw"
    PROCESSED_DATA_DIR: str = "./data/processed"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # 分析参数
    DEFAULT_YEAR: int = 2025
    DEFAULT_REGION: str = "深圳"
    DEFAULT_INDUSTRY: str = "半导体"
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }


def setup_logging(settings: Settings):
    """配置日志系统"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if settings.LOG_FILE:
        handlers.append(logging.FileHandler(settings.LOG_FILE, encoding='utf-8'))
    
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        handlers=handlers
    )


settings = Settings()
setup_logging(settings)

if settings.SECRET_KEY == "dev-secret-key-change-in-production":
    import warnings
    warnings.warn(
        "SECRET_KEY is using the default development value. "
        "Set the SECRET_KEY environment variable for production.",
        RuntimeWarning
    )

if settings.ALGORITHM == "RS256" and not settings.SECRET_KEY.startswith("-----BEGIN"):
    import warnings
    warnings.warn(
        "SECRET_KEY does not appear to be an RSA private key. "
        "For RS256, a valid RSA key pair is required.",
        RuntimeWarning
    )

Path("data").mkdir(parents=True, exist_ok=True)
