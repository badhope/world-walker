"""
数据 API 路由
"""

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel



router = APIRouter(prefix="/data", tags=["数据管理"])


# 模拟数据库
sample_data = []


class IndicatorCreate(BaseModel):
    """创建指标请求"""

    code: str
    name: str
    value: float
    unit: str | None = None
    year: int | None = None
    month: int | None = None
    quarter: int | None = None
    category: str | None = None
    region: str | None = None
    source: str | None = None


class Indicator(IndicatorCreate):
    """指标响应"""

    id: int
    timestamp: str


@router.post("/", response_model=Indicator, summary="创建指标记录")
def create_indicator(
    indicator: IndicatorCreate,
):
    """创建单条经济指标记录(需要管理员鉴权)"""
    new_id = len(sample_data) + 1
    new_indicator = Indicator(id=new_id, timestamp=datetime.now().isoformat(), **indicator.model_dump())
    sample_data.append(new_indicator)
    return new_indicator


@router.get("/", summary="查询指标列表")
def list_indicators(
    code: str | None = Query(None, description="指标代码"),
    category: str | None = Query(None, description="类别"),
    year: int | None = Query(None, description="年份"),
    region: str | None = Query(None, description="地区"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
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
    items = filtered[start : start + page_size]

    return {"data": items, "total": total, "page": page, "page_size": page_size}


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
def list_codes(category: str | None = Query(None)):
    """获取所有指标代码"""
    filtered = sample_data
    if category:
        filtered = [d for d in filtered if d.category == category]

    codes = list({(d.code, d.name) for d in filtered if d.code})
    return {"codes": [{"code": c[0], "name": c[1]} for c in codes]}


def get_example_data_path(filename: str):
    """获取示例数据文件路径"""
    base_dir = Path(__file__).parent.parent.parent.parent
    return base_dir / "examples" / "shenzhen_semiconductor_2025" / "data" / filename


@router.get("/basic", summary="获取基础数据")
def get_basic_data():
    """获取深圳半导体产业基础数据"""
    try:
        data_file = get_example_data_path("basic_data.json")
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)

        return {"region": "深圳", "industry": "半导体", "year": 2025, "data": data}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trend", summary="获取趋势数据")
def get_trend_data(
    region: str = Query("深圳"),
    industry: str = Query("半导体"),
    start_year: int = Query(2020),
    end_year: int = Query(2025),
):
    """获取产业趋势数据"""
    try:
        # 返回模拟趋势数据
        years = list(range(start_year, end_year + 1))
        gdp = [30800, 32400, 30800, 32800, 35800, 36800]
        industry_output = [6800, 8200, 9600, 11000, 12000, 12800]

        return {
            "years": years,
            "series": [
                {"name": "GDP (亿元)", "data": gdp[: len(years)]},
                {"name": "半导体产值 (亿元)", "data": industry_output[: len(years)]},
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/map", summary="获取地图数据")
def get_map_data(indicator: str = Query("output"), year: int = Query(2025)):
    """获取产业地图数据"""
    return {
        "indicator": indicator,
        "year": year,
        "values": [
            {"name": "深圳", "value": 12000},
            {"name": "上海", "value": 13500},
            {"name": "北京", "value": 11800},
            {"name": "广州", "value": 8900},
            {"name": "苏州", "value": 7200},
            {"name": "无锡", "value": 5600},
            {"name": "成都", "value": 4500},
            {"name": "西安", "value": 3800},
        ],
        "geoJson": {},  # 实际项目需加载真实的GeoJSON
    }

