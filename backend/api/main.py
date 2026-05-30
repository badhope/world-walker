"""
国家经济数据分析平台 - FastAPI 后端
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from backend.api.routes import data_router, analysis_router, inference_router
from backend.api.routes import interactive_router, websocket_router, cities_router, real_data_router

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
## 区域产业经济分析平台 API

### 核心功能

- **数据管理**: 经济指标数据的增删改查
- **企业端分析**: 营商成本、供应链配套、政策红利分析
- **政府端分析**: 财政杠杆、产业带动、产业链分析
- **经济模型**: 菲利普斯曲线、奥肯定律、柯布-道格拉斯等经典模型
- **可视化**: 多种图表展示分析结果

### 使用说明

1. 使用 `/api/v1/data/*` 管理数据
2. 使用 `/api/v1/analysis/*` 进行产业分析
3. 使用 `/api/v1/inference/*` 运行经济模型
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(data_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(inference_router, prefix=settings.API_V1_STR)
app.include_router(interactive_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router, prefix=settings.API_V1_STR)
app.include_router(cities_router, prefix=settings.API_V1_STR)
app.include_router(real_data_router)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
