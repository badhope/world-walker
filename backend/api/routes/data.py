"""
数据 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/data", tags=["数据管理"])


# 模拟数据库
sample_data = []


class IndicatorCreate(BaseModel):
    """创建指标请求"""
    code: str
    name: str
    value: float
    unit: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    category: Optional[str] = None
    region: Optional[str] = None
    source: Optional[str] = None


class Indicator(IndicatorCreate):
    """指标响应"""
    id: int
    timestamp: str


@router.post("/", response_model=Indicator, summary="创建指标记录")
def create_indicator(indicator: IndicatorCreate):
    """创建单条经济指标记录"""
    new_id = len(sample_data) + 1
    new_indicator = Indicator(
        id=new_id,
        timestamp=datetime.now().isoformat(),
        **indicator.model_dump()
    )
    sample_data.append(new_indicator)
    return new_indicator


@router.get("/", summary="查询指标列表")
def list_indicators(
    code: Optional[str] = Query(None, description="指标代码"),
    category: Optional[str] = Query(None, description="类别"),
    year: Optional[int] = Query(None, description="年份"),
    region: Optional[str] = Query(None, description="地区"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """查询经济指标列表"""
    filtered = sample_data
    if code:
        filtered = [d for d in filtered if d.code == code]
    if category:
        filtered = [d for d in filtered if d.category == category]
    if year:
        filtered = [d for d in filtered if d.year == year]
    if region:
        filtered = [d for d in filtered if d.region == region]
    
    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start:start + page_size]
    
    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{indicator_id}", response_model=Indicator, summary="获取单个指标")
def get_indicator(indicator_id: int):
    """获取单个经济指标详情"""
    indicator = next((d for d in sample_data if d.id == indicator_id), None)
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")
    return indicator


@router.get("/categories/list", summary="获取所有类别")
def list_categories():
    """获取所有指标类别"""
    categories = list(set(d.category for d in sample_data if d.category))
    return {"categories": categories}


@router.get("/codes/list", summary="获取所有指标代码")
def list_codes(
    category: Optional[str] = Query(None)
):
    """获取所有指标代码"""
    filtered = sample_data
    if category:
        filtered = [d for d in filtered if d.category == category]
    
    codes = list({(d.code, d.name) for d in filtered if d.code})
    return {"codes": [{"code": c[0], "name": c[1]} for c in codes]}
