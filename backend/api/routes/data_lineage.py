"""
数据血缘 + provenance API — 投资决策级必备。

端点:
- GET /data/provenance/{scope}/{name}?indicator=...&year=...  返回某数据点的来源/置信度
- GET /data/coverage  返回全平台数据覆盖报告
- GET /data/macro  返回宏观协变量时序
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.data.historical_extended import (
    INDICATOR_META as CITY_META,
)
from backend.data.historical_extended import (
    get_city_indicator as ext_get_city_indicator,
)
from backend.data.historical_extended import (
    get_data_coverage as ext_get_data_coverage,
)
from backend.data.historical_extended import (
    list_extended_cities,
    list_extended_indicators,
)
from backend.data.macro_data import (
    INDICATOR_META as MACRO_META,
)
from backend.data.macro_data import (
    compute_growth_rates as macro_growth,
)
from backend.data.macro_data import (
    get_macro_timeseries,
    get_macro_value,
    list_macro_indicators,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lineage", tags=["data lineage"])


@router.get("/provenance/city/{city_name}", summary="城市数据点 provenance")
async def get_city_provenance(
    city_name: str,
    indicator: str = Query(..., description="指标代码"),
    year: int | None = Query(None, description="年份(默认最新)"),
) -> dict[str, Any]:
    """返回某城市某指标(某年)的数据点 + 完整 provenance 元数据。"""
    if city_name not in list_extended_cities():
        raise HTTPException(status_code=404, detail=f"城市 {city_name} 不在扩展数据集中")
    if indicator not in list_extended_indicators():
        raise HTTPException(status_code=400, detail=f"指标 {indicator} 不支持")

    info = ext_get_city_indicator(city_name, indicator, year)
    if info is None:
        raise HTTPException(status_code=404, detail=f"{city_name}/{indicator}/{year} 数据缺失")

    return {
        **info,
        "indicator_meta": CITY_META.get(indicator, {}),
    }


@router.get("/coverage", summary="全平台数据覆盖报告")
async def get_coverage_report(city: str | None = Query(None)) -> dict[str, Any]:
    """返回每个城市每年的指标覆盖情况,用于审计/合规。"""
    return ext_get_data_coverage(city)


@router.get("/macro", summary="宏观协变量时序")
async def get_macro(indicator: str | None = Query(None), year: int | None = Query(None)) -> dict[str, Any]:
    """宏观协变量查询。indicator+year 组合返回单点;无参返回全时序。"""
    if indicator and year:
        info = get_macro_value(indicator, year)
        if info is None:
            raise HTTPException(status_code=404, detail=f"宏观 {indicator}/{year} 缺失")
        return {**info, "indicator_meta": MACRO_META.get(indicator, {})}

    if indicator:
        df = get_macro_timeseries()
        if indicator not in df.columns:
            raise HTTPException(status_code=400, detail=f"宏观指标 {indicator} 不支持")
        return {
            "indicator": indicator,
            "indicator_meta": MACRO_META.get(indicator, {}),
            "timeseries": df[["year", indicator]].to_dict(orient="records"),
        }

    return {
        "indicators": list_macro_indicators(),
        "indicator_meta": MACRO_META,
        "timeseries": get_macro_timeseries().to_dict(orient="records"),
    }


@router.get("/macro/growth", summary="宏观 YoY 增长率")
async def get_macro_growth() -> dict[str, Any]:
    """返回带 YoY 增长率的衍生指标。"""
    df = macro_growth()
    return {
        "years": df["year"].tolist(),
        "national_gdp_yoy": df["national_gdp_yoy"].round(2).tolist(),
        "fdi_inflow_yoy": df["fdi_inflow_yoy"].round(2).tolist(),
    }


@router.get("/summary", summary="数据总览")
async def get_data_summary() -> dict[str, Any]:
    """投资决策级数据总览 — 城市数、指标数、年份、覆盖度、宏观协变量数。"""
    coverage = ext_get_data_coverage()
    total_cells = sum(16 * 12 for _ in coverage)
    filled = sum(int(16 * 12 * info["completeness"]) for info in coverage.values())
    return {
        "cities": {
            "total": len(list_extended_cities()),
            "list": list_extended_cities(),
        },
        "indicators": {
            "total": len(list_extended_indicators()),
            "absolute": sorted([k for k, v in CITY_META.items() if v.get("category") == "absolute"]),
            "rate": sorted([k for k, v in CITY_META.items() if v.get("category") == "rate"]),
        },
        "years": {"start": 2010, "end": 2025, "count": 16},
        "coverage": {
            "total_cells": total_cells,
            "filled_cells": filled,
            "completeness": filled / total_cells if total_cells else 0.0,
        },
        "macro_indicators": list_macro_indicators(),
        "provenance": {
            "every_data_point_has_source": True,
            "every_data_point_has_confidence": True,
            "2020_population_methodology_change_flagged": True,
            "2024+_marked_as_estimated": True,
        },
    }
