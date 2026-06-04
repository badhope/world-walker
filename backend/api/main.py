"""
FastAPI backend for the regional economic analysis platform.

Routes are split across `backend.api.routes.*` and mounted under
`settings.API_V1_STR`. The single-page UI is served from
`/dashboard` and `/app` so the API and the UI can share one origin
in production.
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

from backend.api.limiter import limiter
from backend.api.routes import (
    analysis_router,
    analysis_v3_router,
    cities_router,
    cities_v2_router,
    data_lineage_router,
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
from backend.api.security_headers import SecurityHeadersMiddleware
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s v%s", settings.PROJECT_NAME, settings.VERSION)
    yield
    logger.info("shutting down")


# 是否启用 HSTS(仅在 HTTPS 站点打开,避免 HTTP 环境被卡死)
ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() in {"1", "true", "yes"}


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API for multi-city economic comparison, enterprise "
    "site selection, sales forecasting, and government policy evaluation.",
    contact={"name": "Regional Economic Analysis", "email": "contact@example.com"},
    license_info={"name": "GPL-3.0-or-later", "url": "https://www.gnu.org/licenses/gpl-3.0.html"},
    openapi_tags=[
        {"name": "城市数据", "description": "Multi-city economic data."},
        {"name": "产业分析", "description": "Industry / enterprise analysis."},
        {"name": "城市对比", "description": "Side-by-side city comparison."},
        {"name": "时间序列", "description": "Time-series forecasting."},
        {"name": "数据采集", "description": "Real-data ingestion."},
        {"name": "认证", "description": "Authentication and authorisation."},
        {"name": "WebSocket", "description": "Real-time push channel."},
        {"name": "系统", "description": "Health, metadata and static assets."},
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ----- 中间件顺序:外层先执行 -----
# 1) 安全响应头(放最外,影响所有响应包括 4xx/5xx)
app.add_middleware(SecurityHeadersMiddleware, hsts=ENABLE_HSTS)

# 2) CORS(显式白名单,移除占位 0.0.0.0)
allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# 3) TrustedHost:从环境收紧,默认不含 0.0.0.0
_trusted_hosts_env = os.getenv("TRUSTED_HOSTS")
if _trusted_hosts_env:
    _allowed_hosts = [h.strip() for h in _trusted_hosts_env.split(",") if h.strip()]
else:
    # 默认只信 localhost + 测试;生产必须显式设 TRUSTED_HOSTS
    # 0.0.0.0 不在白名单 — 它是绑定地址,不是 Host 头合法值
    _allowed_hosts = [
        "localhost",
        "127.0.0.1",
        "*.local",
        "testserver",  # Starlette TestClient
        "testclient",  # pytest
    ]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)


# 4) 全局限流:每个 IP 每分钟 120 次(可经 RATE_LIMIT_PER_MIN 调)
_rate = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))


@app.middleware("http")
async def _global_rate_limit(request: Request, call_next):
    """全局 IP+路径 限流中间件"""
    try:
        limiter._apply(request, _rate, 60)
    except Exception as exc:  # HTTPException from limiter
        from fastapi.responses import JSONResponse

        status_code = getattr(exc, "status_code", 429)
        return JSONResponse(
            status_code=status_code,
            content={"detail": getattr(exc, "detail", "Rate limited")},
            headers=getattr(exc, "headers", None) or {"Retry-After": "60"},
        )
    return await call_next(request)


# ----- 路由挂载 -----
# 注意:analysis_router 与 analysis_v3_router 都用 prefix="/analysis",
# cities_router 与 cities_v2_router 都用 prefix="/cities"。只要 method+path
# 不重复就能共存。重复项已在代码里拆开(/compare 改为 POST 唯一)。
for router in (
    auth_router,
    (data_router, settings.API_V1_STR),
    (analysis_router, settings.API_V1_STR),
    (inference_router, settings.API_V1_STR),
    (interactive_router, settings.API_V1_STR),
    (websocket_router, settings.API_V1_STR),
    (cities_router, settings.API_V1_STR),
    (cities_v2_router, settings.API_V1_STR),
    (forecast_router, settings.API_V1_STR),
    (analysis_v3_router, settings.API_V1_STR),
    (ml_router, settings.API_V1_STR),
    (data_lineage_router, settings.API_V1_STR),
):
    if isinstance(router, tuple):
        app.include_router(router[0], prefix=router[1])
    else:
        app.include_router(router)

app.include_router(real_data_router)
app.include_router(database_router)
app.include_router(static_router)

frontend_index = Path(__file__).parent.parent.parent / "frontend" / "index.html"


@app.get("/dashboard", tags=["页面"])
async def get_dashboard():
    if frontend_index.exists():
        return FileResponse(frontend_index, media_type="text/html")
    return {"error": "frontend not built", "hint": "frontend/index.html missing"}


@app.get("/app", tags=["页面"])
async def get_app():
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


@app.get("/health", tags=["健康检查"])
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
    }


# favicon:用真实的 .ico 文件优先,否则返回占位 SVG
FAVICON_ICO_PATH = Path(__file__).parent.parent.parent / "frontend" / "favicon.ico"
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" rx="20" fill="#2563eb"/>'
    '<text x="50" y="65" font-size="52" text-anchor="middle" fill="white" '
    'font-family="Arial" font-weight="bold">N</text>'
    "</svg>"
)


@app.get("/favicon.ico", tags=["静态资源"], include_in_schema=False)
def favicon():
    if FAVICON_ICO_PATH.exists():
        return FileResponse(FAVICON_ICO_PATH, media_type="image/x-icon")
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


def run() -> None:
    """Console-script entry point (`rea-api` / `regional-stats-api`)."""
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
