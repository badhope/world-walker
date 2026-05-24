"""
国家经济数据分析平台 - 统一配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """应用配置"""
    # 基础信息
    PROJECT_NAME: str = "国家经济数据分析平台"
    VERSION: str = "4.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./data/national_stats.db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
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
    
    # 安全
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

# 确保目录存在
Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.EXPORT_DIR).mkdir(parents=True, exist_ok=True)
