"""
时间序列预测 API - 数据分析师作品集

支持的"用过去的发展找规律"场景:
- 单城市 × 单指标预测:`GET /forecast/indicator/{city_name}?indicator=fiscal_revenue`
- 单城市 GDP 预测(兼容旧端点):`GET /forecast/gdp/{city_name}`
- 多城市 × 单指标预测对比:`POST /forecast/compare`
- 单省份 × 单指标聚合 + 预测:`POST /forecast/province/{province_name}`
- 全 7 省份 × 单指标批量报告:`POST /forecast/province/all`
- 完整预测报告:`GET /forecast/report/full`

模型双轨:
1. statsforecast.AutoARIMA(首选;依赖缺失时透明 fallback)
2. sklearn LinearRegression + t 分布预测区间(基于残差标准误 + 杠杆修正)
   真实给出 lower_95 / upper_95,而不是把带宽压成 0 的占位。
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.core.province_aggregator import (
    SUPPORTED_INDICATORS,
    forecast_all_provinces,
    forecast_city_indicator,
    forecast_province_indicator,
)
from backend.data.city_data import get_all_cities, get_all_forecast_cities

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["预测分析"])


# --------------------------------------------------------------------------- #
# 请求模型
# --------------------------------------------------------------------------- #


class CompareRequest(BaseModel):
    """多城市 × 单指标 预测对比"""

    city_names: list[str] = Field(..., min_length=1, max_length=20, description="城市名称列表")
    indicator: str = Field("gdp", description="要预测的指标,默认 gdp")
    forecast_years: int = Field(5, ge=1, le=20, description="预测年数")


class ProvinceRequest(BaseModel):
    """省级聚合 + 预测"""

    indicator: str = Field("gdp", description="要预测的指标")
    forecast_years: int = Field(5, ge=1, le=20, description="预测年数")


# --------------------------------------------------------------------------- #
# 端点
# --------------------------------------------------------------------------- #


@router.get("/indicators", summary="列出所有支持的预测指标")
async def list_supported_indicators() -> dict[str, Any]:
    """列出所有可作为预测目标的指标(用于前端下拉框)"""
    from backend.core.province_aggregator import _ABSOLUTE_INDICATORS, _RATE_INDICATORS

    return {
        "supported_indicators": SUPPORTED_INDICATORS,
        "absolute_indicators": sorted(_ABSOLUTE_INDICATORS),
        "rate_indicators": sorted(_RATE_INDICATORS),
        "total": len(SUPPORTED_INDICATORS),
    }


@router.get("/provinces", summary="列出所有支持预测的省份")
async def list_supported_provinces() -> dict[str, Any]:
    """从 cities.yaml 反推省份→城市映射,列出可预测的省份。"""
    from backend.core.province_aggregator import get_province_index

    idx = get_province_index()
    return {
        "provinces": [
            {"province": p, "cities": cities, "city_count": len(cities)} for p, cities in sorted(idx.items())
        ],
        "total_provinces": len(idx),
    }


@router.get("/gdp/{city_name}", summary="[兼容] 预测城市 GDP")
async def forecast_city_gdp(
    city_name: str,
    forecast_years: int = Query(5, ge=1, le=20, description="预测年数"),
) -> dict[str, Any]:
    """
    兼容旧端点:预测指定城市 GDP。
    内部走新的 forecast_city_indicator 逻辑,真实置信区间。
    """
    if city_name not in get_all_cities():
        raise HTTPException(status_code=404, detail=f"城市 {city_name} 数据未找到")

    result = forecast_city_indicator(city_name, "gdp", forecast_years)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    return {
        "city": city_name,
        "indicator": "gdp",
        "historical_years": result["historical_years"],
        "historical_data": [
            {"year": y, "gdp": v} for y, v in zip(result["historical_years"], result["historical_values"])
        ],
        "forecast_years": result["forecast_years"],
        "forecast_data": [
            {
                "year": y,
                "forecast": round(v, 4),
                "forecast_lower": round(lo, 4),
                "forecast_upper": round(hi, 4),
            }
            for y, v, lo, hi in zip(
                result["forecast_years"],
                result["forecast_values"],
                result["lower_95"],
                result["upper_95"],
            )
        ],
        "forecast_method": result["method"],
        "model_metrics": result["metrics"],
        "growth": result["growth"],
        "note": "真实置信区间(非零带宽占位);fallback 走 OLS + t 分布 PI",
    }


@router.get("/indicator/{city_name}", summary="预测城市任意指标")
async def forecast_city_indicator_endpoint(
    city_name: str,
    indicator: str = Query("gdp", description=f"指标代码,支持: {', '.join(SUPPORTED_INDICATORS)}"),
    forecast_years: int = Query(5, ge=1, le=20, description="预测年数"),
) -> dict[str, Any]:
    """
    预测指定城市 × 任意指标的未来 years 年值。
    """
    if city_name not in get_all_cities():
        raise HTTPException(status_code=404, detail=f"城市 {city_name} 数据未找到")
    if indicator not in SUPPORTED_INDICATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Indicator '{indicator}' not supported. Use /forecast/indicators to list.",
        )

    result = forecast_city_indicator(city_name, indicator, forecast_years)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@router.post("/compare", summary="多城市 × 单指标 预测对比")
async def compare_city_forecasts(request: CompareRequest) -> dict[str, Any]:
    """
    对比多个城市 × 同一指标 的预测结果。
    """
    if request.indicator not in SUPPORTED_INDICATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Indicator '{request.indicator}' not supported.",
        )

    valid_cities = [c for c in request.city_names if c in get_all_forecast_cities()]
    if not valid_cities:
        raise HTTPException(status_code=400, detail="未提供有效的城市名称")

    forecasts: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for city in valid_cities:
        r = forecast_city_indicator(city, request.indicator, request.forecast_years)
        if "error" in r:
            errors[city] = r["error"]
            continue
        forecasts[city] = {
            "historical_values": r["historical_values"],
            "historical_years": r["historical_years"],
            "forecast_years": r["forecast_years"],
            "forecast_values": r["forecast_values"],
            "lower_95": r["lower_95"],
            "upper_95": r["upper_95"],
            "method": r["method"],
            "metrics": r["metrics"],
            "growth": r["growth"],
        }

    # 对比表:末年预测值 + CAGR
    comparison = []
    for city, fc in forecasts.items():
        if fc["forecast_values"]:
            comparison.append(
                {
                    "city": city,
                    "latest_value": fc["historical_values"][-1] if fc["historical_values"] else None,
                    "forecast_value": fc["forecast_values"][-1],
                    "forecast_cagr_pct": fc["growth"]["forecast_cagr_pct"],
                    "method": fc["method"],
                }
            )
    comparison.sort(key=lambda r: r["forecast_value"] or 0, reverse=True)

    return {
        "indicator": request.indicator,
        "cities": list(forecasts.keys()),
        "errors": errors,
        "forecast_years": request.forecast_years,
        "forecasts": forecasts,
        "comparison": comparison,
        "methodology": "AutoARIMA (首选) / LinearRegression + t 分布 PI (fallback)",
    }


@router.get("/province/all", summary="全 7 省 × 单指标 批量预测报告")
async def forecast_all_provinces_endpoint(
    indicator: str = Query("gdp", description="要预测的指标"),
    forecast_years: int = Query(5, ge=1, le=20, description="预测年数"),
) -> dict[str, Any]:
    """
    一次性对所有 7 个省份 × 1 个指标做"过去发展找规律 + 未来预测"。

    适合:
    - 数学建模课程的"按省份 GDP 演化"展示
    - 政策评估报告的横向对比
    - 政府决策者一页看完全国趋势

    注意:此路由必须在 `/province/{province_name}` 之前,否则会被路径参数
    `province_name="all"` 抢先匹配。FastAPI 按声明顺序匹配,先到先得。
    """
    if indicator not in SUPPORTED_INDICATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Indicator '{indicator}' not supported.",
        )

    return forecast_all_provinces(indicator, forecast_years)


@router.post("/province/{province_name}", summary="省级 × 单指标 聚合 + 预测")
async def forecast_province_endpoint(
    province_name: str,
    request: ProvinceRequest,
) -> dict[str, Any]:
    """
    对指定省份 × 指定指标,先把省内各城市历史数据按"绝对量求和/率加权"
    聚合,再对未来 years 年做预测。
    """
    if request.indicator not in SUPPORTED_INDICATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Indicator '{request.indicator}' not supported.",
        )

    result = forecast_province_indicator(province_name, request.indicator, request.forecast_years)
    if "error" in result:
        # 404: 省份不在; 503: 数据缺失
        status = 404 if "not in registry" in result["error"] else 503
        raise HTTPException(status_code=status, detail=result["error"])
    return result


@router.get("/report/full", summary="完整预测报告(8 城 × 1 指标)")
async def get_full_forecast_report(
    indicator: str = Query("gdp", description="默认 gdp"),
    forecast_years: int = Query(5, ge=1, le=20),
) -> dict[str, Any]:
    """
    城市级完整预测报告 — 8 个城市 × 单指标批量预测。
    """
    if indicator not in SUPPORTED_INDICATORS:
        raise HTTPException(status_code=400, detail=f"Indicator '{indicator}' not supported.")

    cities = get_all_forecast_cities()
    city_results: dict[str, Any] = {}
    for city in cities:
        r = forecast_city_indicator(city, indicator, forecast_years)
        if "error" not in r:
            city_results[city] = r

    # 增速最快/最慢
    comparison = sorted(
        [
            {
                "city": c,
                "latest_value": r["historical_values"][-1],
                "forecast_value": r["forecast_values"][-1],
                "cagr_pct": r["growth"]["forecast_cagr_pct"],
                "method": r["method"],
            }
            for c, r in city_results.items()
        ],
        key=lambda x: x["cagr_pct"],
        reverse=True,
    )

    return {
        "report_title": f"主要城市 {indicator} 预测对比分析报告",
        "indicator": indicator,
        "cities": list(city_results.keys()),
        "forecast_horizon_years": forecast_years,
        "city_forecasts": city_results,
        "comparison_by_cagr": comparison,
        "methodology": {
            "primary_method": "AutoARIMA (statsforecast) / LinearRegression + t 分布 PI",
            "note": "真实预测区间;statsforecast 不可用时透明 fallback 到 OLS+t",
        },
    }
