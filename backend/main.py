"""
国家经济数据分析平台 - FastAPI 后端
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from backend.core.config import settings
from backend.core.database import init_db, engine
from backend.api.routes import data_router, inference_router, scrape_router
from sqlalchemy import text

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
    
    # 初始化数据库
    init_db()
    logger.info("数据库初始化完成")
    
    yield
    
    logger.info("关闭应用...")


# 创建应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## 国家经济数据综合分析平台 API

### 核心功能

- **数据采集**: 从官方数据源自动获取经济数据
- **指标管理**: 增删改查经济指标数据
- **指标推演**: 基于经济学公式推算关联指标
- **经济模型**: 菲利普斯曲线、奥肯定律、柯布-道格拉斯等经典模型

### 数据源

- 国家统计局 (NBS)
- 人民银行 (PBC)
- 海关总署
- 财政部 (MOF)

### 使用说明

1. 先调用 `/api/v1/scrape/` 采集数据
2. 使用 `/api/v1/inference/calculate` 进行指标推演
3. 或使用 `/api/v1/inference/models/*` 运行经济模型
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
app.include_router(inference_router, prefix=settings.API_V1_STR)
app.include_router(scrape_router, prefix=settings.API_V1_STR)


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
    # 检查数据库
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
