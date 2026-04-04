"""
数据 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.core.database import get_db, EconomicIndicator
from backend.models.schemas import (
    IndicatorCreate, Indicator, IndicatorResponse,
    IndicatorBatchCreate, MessageResponse
)

router = APIRouter(prefix="/indicators", tags=["经济指标"])


@router.post("/", response_model=Indicator, summary="创建指标记录")
def create_indicator(indicator: IndicatorCreate, db: Session = Depends(get_db)):
    """创建单条经济指标记录"""
    db_indicator = EconomicIndicator(**indicator.model_dump())
    db.add(db_indicator)
    db.commit()
    db.refresh(db_indicator)
    return db_indicator


@router.post("/batch", response_model=MessageResponse, summary="批量创建指标")
def create_indicators_batch(batch: IndicatorBatchCreate, db: Session = Depends(get_db)):
    """批量创建经济指标记录"""
    indicators = [EconomicIndicator(**ind.model_dump()) for ind in batch.indicators]
    db.add_all(indicators)
    db.commit()
    return MessageResponse(
        message="批量创建成功",
        detail=f"已创建 {len(indicators)} 条记录"
    )


@router.get("/", response_model=IndicatorResponse, summary="查询指标列表")
def list_indicators(
    code: Optional[str] = Query(None, description="指标代码"),
    category: Optional[str] = Query(None, description="类别"),
    year: Optional[int] = Query(None, description="年份"),
    region: Optional[str] = Query(None, description="地区"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """查询经济指标列表"""
    query = db.query(EconomicIndicator)
    
    if code:
        query = query.filter(EconomicIndicator.code == code)
    if category:
        query = query.filter(EconomicIndicator.category == category)
    if year:
        query = query.filter(EconomicIndicator.year == year)
    if region:
        query = query.filter(EconomicIndicator.region == region)
    
    total = query.count()
    items = query.order_by(EconomicIndicator.year.desc(), EconomicIndicator.month.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    return IndicatorResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{indicator_id}", response_model=Indicator, summary="获取单个指标")
def get_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """获取单个经济指标详情"""
    indicator = db.query(EconomicIndicator).filter(EconomicIndicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")
    return indicator


@router.delete("/{indicator_id}", response_model=MessageResponse, summary="删除指标")
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """删除经济指标"""
    indicator = db.query(EconomicIndicator).filter(EconomicIndicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")
    db.delete(indicator)
    db.commit()
    return MessageResponse(message="删除成功")


@router.get("/categories/list", summary="获取所有类别")
def list_categories(db: Session = Depends(get_db)):
    """获取所有指标类别"""
    categories = db.query(EconomicIndicator.category).distinct().all()
    return {"categories": [c[0] for c in categories if c[0]]}


@router.get("/codes/list", summary="获取所有指标代码")
def list_codes(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取所有指标代码"""
    query = db.query(EconomicIndicator.code, EconomicIndicator.name).distinct()
    if category:
        query = query.filter(EconomicIndicator.category == category)
    codes = query.all()
    return {"codes": [{"code": c[0], "name": c[1]} for c in codes if c[0]]}
