"""
真实城市数据 API - 数据分析师作品集
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.data.city_data import (
    compare_cities,
    generate_data_quality_report,
    get_all_cities,
    get_city_data,
    get_data_source_info,
    get_historical_data,
    get_score_benchmarks,
    get_score_weights,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cities", tags=["城市数据"])


@router.get("/list", summary="获取所有城市列表")
async def list_cities() -> dict[str, Any]:
    """获取系统支持的所有城市列表"""
    return {"cities": get_all_cities(), "total": len(get_all_cities())}


@router.get("/{city_name}", summary="获取指定城市详情")
async def get_city_detail(city_name: str) -> dict[str, Any]:
    """
    获取指定城市的详细数据

    - **city_name**: 城市名称（深圳/上海/成都）
    """
    data = get_city_data(city_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"城市 {city_name} 数据未找到")

    data_source = get_data_source_info().get(city_name, {})

    return {"city": city_name, "data": data, "data_source": data_source}


@router.get("/{city_name}/historical", summary="获取城市历史数据")
async def get_city_historical(city_name: str) -> dict[str, Any]:
    """
    获取指定城市的历史时间序列数据

    - **city_name**: 城市名称
    """
    data = get_historical_data(city_name)
    if data is None or (hasattr(data, "empty") and data.empty) or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"城市 {city_name} 历史数据未找到")

    if hasattr(data, "to_dict"):
        records = data.to_dict(orient="records")
    else:
        records = data

    return {"city": city_name, "years": [2020, 2021, 2022, 2023, 2024, 2025], "historical_data": records}


@router.post("/compare", summary="对比多个城市")
async def compare_multiple_cities(city_names: list[str]) -> dict[str, Any]:
    """
    对比多个城市的数据

    - **city_names**: 城市名称列表
    """
    valid_cities = [city for city in city_names if city in get_all_cities()]
    if not valid_cities:
        raise HTTPException(status_code=400, detail="未提供有效的城市名称")

    comparison_result = compare_cities(valid_cities)
    if hasattr(comparison_result, "to_dict"):
        comparison_data = comparison_result.to_dict(orient="records")
    else:
        comparison_data = comparison_result

    return {"cities": valid_cities, "comparison": comparison_data}


@router.get("/benchmarks/scores", summary="获取评分基准")
async def get_scoring_benchmarks() -> dict[str, Any]:
    """
    获取评分系统的基准值

    基准值基于真实城市数据的统计分位数（25%/50%/75%）
    """
    return {
        "benchmarks": get_score_benchmarks(),
        "weights": get_score_weights(),
        "note": "评分基准基于真实城市数据的25%/50%/75%分位数，权重基于对50家半导体制造企业的调研",
    }


@router.get("/quality/report", summary="获取数据质量报告")
async def get_data_quality_report() -> dict[str, Any]:
    """
    获取完整的数据质量评估报告

    包括：
    - 各城市数据质量评分
    - 数据来源说明
    - 更新时间
    """
    return generate_data_quality_report()
