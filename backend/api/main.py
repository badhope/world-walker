"""
区域产业经济分析平台 - FastAPI 后端（数据分析师作品集）
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from backend.api.routes import (
    data_router, analysis_router, inference_router,
    interactive_router, websocket_router, cities_router,
    cities_v2_router, forecast_router, analysis_v3_router,
    real_data_router, database_router, static_router
)
from backend.api.routes.auth import router as auth_router

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"启动 {settings.PROJECT_NAME} v{settings.VERSION}...")
    yield
    logger.info("关闭应用...")


# 创建应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## 区域产业经济分析平台 API - 数据分析师作品集

### 核心功能

- **真实数据采集**: 整合官方统计数据，多源交叉验证
- **探索性数据分析**: 完整EDA流程，描述性统计，相关性分析
- **时间序列预测**: Prophet模型，MAE/MAPE评估
- **企业选址分析**: 基于统计分位数的评分系统
- **数据可视化**: ECharts交互式图表
- **数据质量管理**: 质量评估，数据验证

### 使用说明

1. 使用 `/api/v1/cities/*` 获取真实城市数据
2. 使用 `/api/v1/analysis/enterprise/v3` 进行企业选址分析
3. 使用 `/api/v1/forecast/*` 进行时间序列预测
4. 访问 `/dashboard` 查看交互式分析仪表盘

### 技术亮点

- 评分基准基于真实数据的统计分位数
- 权重基于企业调研
- 完整的单元测试覆盖
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
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
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat()
    }


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" rx="20" fill="#2563eb"/>'
    '<text x="50" y="65" font-size="52" text-anchor="middle" fill="white" '
    'font-family="Arial" font-weight="bold">N</text>'
    '</svg>'
)


@app.get("/favicon.ico", tags=["静态资源"], include_in_schema=False)
def favicon():
    """返回 SVG favicon"""
    from fastapi.responses import Response
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
