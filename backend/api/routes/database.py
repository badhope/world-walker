"""
数据库API路由 - 提供数据持久化相关接口
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/database", tags=["数据库"])


@router.get("/statistics", summary="获取数据库统计信息")
def get_statistics():
    """获取数据库总体统计信息"""
    try:
        db = get_db()
        stats = db.get_statistics()

        return {"status": "success", "data": stats}
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economic-data", summary="获取经济数据")
def get_economic_data(indicator: str = None, start_year: int = None, end_year: int = None, region: str = "全国"):
    """获取经济数据"""
    try:
        db = get_db()
        data = db.get_economic_data(indicator, start_year, end_year, region)

        return {"status": "success", "data": data.to_dict("records") if not data.empty else [], "count": len(data)}
    except Exception as e:
        logger.error(f"获取经济数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enterprise-analysis/history", summary="获取企业分析历史")
def get_enterprise_analysis_history(region: str = None, industry: str = None, limit: int = 10):
    """获取企业分析历史记录"""
    try:
        db = get_db()
        history = db.get_enterprise_analysis_history(region, industry, limit)

        return {"status": "success", "data": history, "count": len(history)}
    except Exception as e:
        logger.error(f"获取企业分析历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
