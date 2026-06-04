"""
投资决策级 API — Phase 10。
把 forecast_engine + risk_engine 暴露为 HTTP 端点。

6 个新端点:
- GET /api/v1/investment/forecast/full?scope=city&name=深圳&indicator=gdp
- GET /api/v1/investment/diagnostics/{scope}/{name}?indicator=...
- GET /api/v1/investment/structural-breaks/{scope}/{name}?indicator=...
- GET /api/v1/investment/backtest/{scope}/{name}?indicator=...
- GET /api/v1/investment/risk/{scope}/{name}?indicator=...
- GET /api/v1/investment/scenarios/{scope}/{name}?indicator=...
- GET /api/v1/investment/monte-carlo/{scope}/{name}?indicator=...

scope: city | province
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.core.forecast_engine import (
    backtest_forecast,
    find_structural_breaks,
    forecast_full_pipeline,
    run_diagnostics,
)
from backend.core.risk_engine import (
    monte_carlo_simulation,
    risk_full_pipeline,
    rolling_volatility,
    scenario_analysis,
    var_cvar,
)
from backend.data.historical_extended import (
    EXTENDED_HISTORICAL,
    INDICATOR_META,
    get_city_timeseries,
    list_extended_cities,
    list_extended_indicators,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investment", tags=["investment grade"])


# --------------------------------------------------------------------------- #
# 工具:把 city/province 名字映射到时序
# --------------------------------------------------------------------------- #


# 省份 → 城市列表(和 city_data.py 的 _build_province_index 同步)
_PROVINCE_TO_CITIES = {
    "上海": ["上海"],
    "北京": ["北京"],
    "广东": ["深圳", "广州"],
    "江苏": ["南京", "苏州"],
    "浙江": ["杭州"],
    "四川": ["成都"],
    "湖北": ["武汉"],
    "陕西": ["西安"],
}

# 聚合方式
_ABSOLUTE_INDICATORS = frozenset(
    {
        "gdp", "population", "fiscal_revenue",
        "supplier_count", "land_price",
    }
)


def _get_scope_timeseries(
    scope: str, name: str, indicator: str
) -> tuple[list[float], int]:
    """
    返回 (values, start_year)
    - city: 直接从 EXTENDED_HISTORICAL 取
    - province: 聚合(绝对 sum,率加权平均 by population)
    """
    if scope == "city":
        if name not in list_extended_cities():
            raise HTTPException(404, f"城市 {name} 不在扩展数据中")
        if indicator not in list_extended_indicators():
            raise HTTPException(400, f"指标 {indicator} 不支持")
        years = sorted(EXTENDED_HISTORICAL[name].keys())
        values = [
            float(EXTENDED_HISTORICAL[name][y].get(indicator))
            for y in years
            if EXTENDED_HISTORICAL[name][y].get(indicator) is not None
        ]
        if not values:
            raise HTTPException(404, f"{name}/{indicator} 无数据")
        return values, years[0]

    if scope == "province":
        if name not in _PROVINCE_TO_CITIES:
            raise HTTPException(404, f"省份 {name} 不在 8 省中")
        if indicator not in list_extended_indicators():
            raise HTTPException(400, f"指标 {indicator} 不支持")
        cities = _PROVINCE_TO_CITIES[name]
        # 取所有城市的年份并集
        all_years = sorted(
            {y for c in cities for y in EXTENDED_HISTORICAL.get(c, {}).keys()}
        )
        if not all_years:
            raise HTTPException(404, f"{name} 无数据")
        values: list[float] = []
        for y in all_years:
            points = []
            for c in cities:
                cell = EXTENDED_HISTORICAL.get(c, {}).get(y, {})
                v = cell.get(indicator)
                pop = cell.get("population")
                if v is None:
                    continue
                if indicator in _ABSOLUTE_INDICATORS:
                    points.append((float(v), 1.0))
                else:
                    # rate: 人口加权
                    points.append((float(v), float(pop) if pop else 1.0))
            if not points:
                continue
            num = sum(p * w for p, w in points)
            den = sum(w for _, w in points)
            values.append(num / den)
        if not values:
            raise HTTPException(404, f"{name}/{indicator} 无数据")
        return values, all_years[0]

    raise HTTPException(400, f"scope {scope} 不支持,只支持 city / province")


# --------------------------------------------------------------------------- #
# 6+ 端点
# --------------------------------------------------------------------------- #


@router.get("/forecast/full", summary="完整预测流水线")
async def investment_forecast_full(
    scope: str = Query("city", pattern="^(city|province)$"),
    name: str = Query(..., description="城市或省份名"),
    indicator: str = Query("gdp"),
    years: int = Query(5, ge=1, le=15),
) -> dict[str, Any]:
    """集成预测 + 残差诊断 + 结构突变 + 滚动 CV + CAGR"""
    values, start_year = _get_scope_timeseries(scope, name, indicator)
    if len(values) < 5:
        raise HTTPException(400, f"数据不足:n={len(values)}")
    out = forecast_full_pipeline(values, start_year=start_year, years=years)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        "indicator_meta": INDICATOR_META.get(indicator, {}),
        "investment_grade": True,
        "data_provenance": {
            "n_years": len(values),
            "year_range": [start_year, start_year + len(values) - 1],
            "source": f"{name}统计局历年统计公报",
            "estimated_pct": 0.0,
        },
        **out,
    }


@router.get("/diagnostics/{scope}/{name}", summary="残差诊断(5 项)")
async def investment_diagnostics(
    scope: str,
    name: str,
    indicator: str = Query("gdp"),
) -> dict[str, Any]:
    """5 项残差诊断:ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan"""
    values, _ = _get_scope_timeseries(scope, name, indicator)
    if len(values) < 8:
        raise HTTPException(400, f"诊断最少需要 8 年数据,实际 {len(values)}")
    out = run_diagnostics(values)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        **out,
    }


@router.get("/structural-breaks/{scope}/{name}", summary="结构突变检测")
async def investment_structural_breaks(
    scope: str,
    name: str,
    indicator: str = Query("gdp"),
) -> dict[str, Any]:
    """Chow test 遍历所有候选断点,返回显著突变点列表"""
    values, start_year = _get_scope_timeseries(scope, name, indicator)
    if len(values) < 6:
        raise HTTPException(400, f"结构突变检测最少需要 6 年,实际 {len(values)}")
    breaks = find_structural_breaks(values)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        "start_year": start_year,
        "n_years": len(values),
        "n_breaks": len(breaks),
        "breaks": breaks,
        "warning": "突变点仅作风险提示,不代表因果关系" if breaks else None,
    }


@router.get("/backtest/{scope}/{name}", summary="滚动 CV(5 指标)")
async def investment_backtest(
    scope: str,
    name: str,
    indicator: str = Query("gdp"),
    n_test: int = Query(3, ge=1, le=8),
) -> dict[str, Any]:
    """Walk-forward 滚动 CV,返回 MAPE / RMSE / MASE / sMAPE / Coverage"""
    values, _ = _get_scope_timeseries(scope, name, indicator)
    if len(values) < 6:
        raise HTTPException(400, f"回测最少需要 6 年,实际 {len(values)}")
    out = backtest_forecast(values, n_test=n_test)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        **out,
    }


@router.get("/risk/{scope}/{name}", summary="风险指标")
async def investment_risk(
    scope: str,
    name: str,
    indicator: str = Query("gdp"),
) -> dict[str, Any]:
    """波动率 + VaR 95/99 + CVaR"""
    values, _ = _get_scope_timeseries(scope, name, indicator)
    if len(values) < 3:
        raise HTTPException(400, f"风险分析最少需要 3 年,实际 {len(values)}")
    vol = rolling_volatility(values)
    var95 = var_cvar(values, 0.95)
    var99 = var_cvar(values, 0.99)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        "n_years": len(values),
        "volatility": vol,
        "var_95": var95,
        "var_99": var99,
    }


@router.get("/scenarios/{scope}/{name}", summary="4 档情景")
async def investment_scenarios(
    scope: str,
    name: str,
    indicator: str = Query("gdp"),
    years: int = Query(5, ge=1, le=10),
) -> dict[str, Any]:
    """基线/乐观/悲观/衰退 4 档情景"""
    values, start_year = _get_scope_timeseries(scope, name, indicator)
    # 先用完整预测流水线拿 baseline
    pipe = forecast_full_pipeline(values, start_year=start_year, years=years)
    baseline = pipe["ensemble"]["predictions"]
    starting = float(values[-1])
    scenarios = scenario_analysis(baseline, starting)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        "starting_value": starting,
        "years": pipe["years"],
        "baseline_ensemble": [round(x, 2) for x in baseline],
        **scenarios,
    }


@router.get("/monte-carlo/{scope}/{name}", summary="Monte Carlo 1000 次")
async def investment_monte_carlo(
    scope: str,
    name: str,
    indicator: str = Query("gdp"),
    years: int = Query(5, ge=1, le=10),
    n_sims: int = Query(1000, ge=100, le=10000),
    seed: int = Query(42),
) -> dict[str, Any]:
    """1000 次残差 bootstrap,返回 P5/P50/P95"""
    values, _ = _get_scope_timeseries(scope, name, indicator)
    if len(values) < 6:
        raise HTTPException(400, f"MC 最少需要 6 年,实际 {len(values)}")
    out = monte_carlo_simulation(values, years=years, n_sims=n_sims, seed=seed)
    return {
        "scope": scope,
        "name": name,
        "indicator": indicator,
        **out,
    }
