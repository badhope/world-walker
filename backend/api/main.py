"""
Urban Pulse — FastAPI backend for city economic intelligence.

Serves REST API + single-page ECharts dashboard from one process.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s v%s", settings.PROJECT_NAME, settings.VERSION)
    logger.info("loaded %d cities", len(getattr(settings, "CITY_NAMES", [])))
    yield
    logger.info("shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API for multi-city economic comparison, sales forecasting, "
    "and scenario analysis across Chinese cities.",
    license_info={
        "name": "GPL-3.0-or-later",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    openapi_tags=[
        {"name": "城市数据", "description": "Multi-city economic data endpoints."},
        {"name": "分析预测", "description": "Forecasting, risk, and scenario analysis."},
        {"name": "对比分析", "description": "Side-by-side city comparison."},
        {"name": "数据管理", "description": "Data import / export."},
        {"name": "系统", "description": "Health, metadata, and static assets."},
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ----- Middleware -----
ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() in {"1", "true", "yes"}

allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

_trusted_hosts_env = os.getenv("TRUSTED_HOSTS")
if _trusted_hosts_env:
    _allowed_hosts = [h.strip() for h in _trusted_hosts_env.split(",") if h.strip()]
else:
    _allowed_hosts = ["localhost", "127.0.0.1", "*.local", "testserver", "testclient"]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

# ----- Routes -----
from backend.api.routes import (
    analysis_router,
    analysis_v3_router,
    cities_router,
    cities_v2_router,
    data_router,
    forecast_router,
    static_router,
)

app.include_router(data_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(analysis_v3_router, prefix=settings.API_V1_STR)
app.include_router(cities_router, prefix=settings.API_V1_STR)
app.include_router(cities_v2_router, prefix=settings.API_V1_STR)
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(static_router)

frontend_index = Path(__file__).parent.parent.parent / "frontend" / "index.html"


@app.get("/dashboard", tags=["页面"])
async def get_dashboard():
    if frontend_index.exists():
        return FileResponse(frontend_index, media_type="text/html")
    return {"error": "frontend not built", "hint": "frontend/index.html missing"}


@app.get("/", tags=["根路径"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
    }


@app.get("/health", tags=["系统"])
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
    }


# ----- Favicon -----
FAVICON_PATH = Path(__file__).parent.parent.parent / "frontend" / "favicon.ico"
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" rx="20" fill="#2563eb"/>'
    '<text x="50" y="65" font-size="52" text-anchor="middle" fill="white" '
    'font-family="Arial" font-weight="bold">U</text>'
    "</svg>"
)


@app.get("/favicon.ico", tags=["静态资源"], include_in_schema=False)
def favicon():
    if FAVICON_PATH.exists():
        return FileResponse(FAVICON_PATH, media_type="image/x-icon")
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


def run() -> None:
    """Console-script entry point."""
    host = os.getenv("APP_HOST", "127.0.0.1")
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
