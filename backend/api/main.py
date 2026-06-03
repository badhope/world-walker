"""
Regional Industrial Economic Analysis Platform - FastAPI backend.

A production-grade analytics service for:
  - Multi-city economic comparison
  - Enterprise site selection scoring
  - Government industry policy evaluation
  - Time-series forecasting
  - Interactive dashboards
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.api.routes import (
    analysis_router,
    analysis_v3_router,
    cities_router,
    cities_v2_router,
    data_router,
    database_router,
    forecast_router,
    inference_router,
    interactive_router,
    ml_router,
    real_data_router,
    static_router,
    websocket_router,
)
from backend.api.routes.auth import router as auth_router
from config import settings

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    yield
    logger.info("Shutting down...")


# Build the FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## Regional Industrial Economic Analysis Platform API

### Core Capabilities

- **Real data collection** from official statistical sources with multi-source cross-validation
- **Exploratory data analysis** with full EDA pipeline (descriptive stats, correlation analysis)
- **Time-series forecasting** using scikit-learn / statsmodels with MAE/MAPE evaluation
- **Enterprise site selection** scoring based on statistical quantile benchmarks
- **Interactive visualisations** powered by ECharts (radar, heatmap, time-series, gauge)
- **Data quality management** with validation, completeness reports and source attribution

### Quick Start

1. `GET /api/v1/cities/list` — list all supported cities
2. `POST /api/v1/analysis/enterprise` — run enterprise site-selection analysis
3. `POST /api/v1/cities/compare` — compare multiple cities side-by-side
4. `GET /api/v1/forecast/time-series` — produce multi-year time-series forecasts
5. `GET /dashboard` — interactive analysis dashboard
6. `GET /docs` — this interactive Swagger documentation

### Tech Highlights

- **Backend**: FastAPI + Pydantic v2 + Uvicorn
- **Data**: pandas / numpy / scikit-learn / statsmodels
- **Cache**: in-memory with Redis-ready interface
- **Deployment**: Docker / Docker Compose / Systemd / K8s
- **Frontend**: zero-build static HTML + Tailwind CDN + ECharts CDN
""",
    contact={
        "name": "Regional Economic Analysis Team",
        "email": "contact@example.com",
    },
    license_info={
        "name": "GPL-3.0-or-later",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    openapi_tags=[
        {"name": "城市数据", "description": "Multi-city economic data endpoints."},
        {"name": "产业分析", "description": "Industry / enterprise analysis endpoints."},
        {"name": "城市对比", "description": "Side-by-side city comparison endpoints."},
        {"name": "时间序列", "description": "Time-series forecasting endpoints."},
        {"name": "数据采集", "description": "Real-data collection / ingestion endpoints."},
        {"name": "认证", "description": "Authentication and authorisation endpoints."},
        {"name": "WebSocket", "description": "Real-time push channel for live analyses."},
        {"name": "系统", "description": "Health, metadata and static asset endpoints."},
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(data_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(inference_router, prefix=settings.API_V1_STR)
app.include_router(interactive_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router, prefix=settings.API_V1_STR)
app.include_router(cities_router, prefix=settings.API_V1_STR)
app.include_router(cities_v2_router, prefix=settings.API_V1_STR)
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(analysis_v3_router, prefix=settings.API_V1_STR)
app.include_router(real_data_router)
app.include_router(database_router)
app.include_router(static_router)
app.include_router(ml_router, prefix=settings.API_V1_STR)

# 添加静态页面路由
from pathlib import Path

frontend_index = Path(__file__).parent.parent.parent / "frontend" / "index.html"


@app.get("/dashboard", tags=["页面"])
async def get_dashboard():
    """交互式分析仪表盘"""
    if frontend_index.exists():
        return FileResponse(frontend_index, media_type="text/html")
    return {"error": "页面未找到", "hint": "请确保 frontend/index.html 存在"}


@app.get("/app", tags=["页面"])
async def get_app():
    """前端应用主入口"""
    if frontend_index.exists():
        return FileResponse(frontend_index, media_type="text/html")
    return {"error": "页面未找到", "hint": "请确保 frontend/index.html 存在"}


@app.get("/", tags=["根路径"])
def root():
    """API 根路径"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
    }


@app.get("/health", tags=["健康检查"])
def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": settings.VERSION, "timestamp": datetime.now().isoformat()}


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" rx="20" fill="#2563eb"/>'
    '<text x="50" y="65" font-size="52" text-anchor="middle" fill="white" '
    'font-family="Arial" font-weight="bold">N</text>'
    "</svg>"
)


@app.get("/favicon.ico", tags=["静态资源"], include_in_schema=False)
def favicon():
    """Return the SVG favicon."""
    from fastapi.responses import Response

    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


def run() -> None:
    """Entry point used by ``rea-api`` / ``regional-stats-api`` console scripts."""
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    reload = os.getenv("APP_RELOAD", "false").lower() in {"1", "true", "yes"}
    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
    )


if __name__ == "__main__":
    run()
