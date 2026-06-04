"""
Tool executor — 把 LLM 的 tool call 转成对现有 API 的调用,返回 dict。

设计:
- execute_tool(name, args) → dict
- 内部按 name dispatch 到 9 个 _call_* 函数
- 错误用 {"error": "..."} 包装,绝不抛异常(给 LLM 看)
- 内部 _call_* 函数直接调 backend.core.* 或读数据层(不绕 HTTP)
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 内部调用 — 直接复用 forecast_engine / risk_engine / data_layer
# --------------------------------------------------------------------------- #


def _call_forecast(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.forecast_engine import forecast_full_pipeline
    from backend.data.historical_extended import get_city_timeseries, get_province_timeseries

    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if not values:
        return {"error": f"No data for {scope}={name} indicator={indicator}"}
    out = forecast_full_pipeline(values, start_year=2010, years=years)
    # 简化:只返回 ensemble + diagnostics + backtest 摘要
    return {
        "ensemble": out.get("ensemble"),
        "diagnostics_verdict": out.get("diagnostics", {}).get("verdict"),
        "backtest_mape": out.get("backtest", {}).get("mape"),
        "arima_method": out.get("models", {}).get("arima", {}).get("method"),
    }


def _call_diagnostics(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.forecast_engine import run_diagnostics
    from backend.data.historical_extended import get_city_timeseries, get_province_timeseries

    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for diagnostics"}
    return run_diagnostics(values, order=(1, 1, 0))


def _call_backtest(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.forecast_engine import backtest_forecast
    from backend.data.historical_extended import get_city_timeseries, get_province_timeseries

    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 8:
        return {"error": "insufficient data for backtest"}
    return backtest_forecast(values, order=(1, 1, 0))


def _call_risk(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.risk_engine import risk_full_pipeline
    from backend.data.historical_extended import get_city_timeseries, get_province_timeseries

    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for risk"}
    baseline = values[-5:]
    return risk_full_pipeline(values, baseline, starting_value=values[-1], n_sims=200)


def _call_scenarios(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.forecast_engine import forecast_full_pipeline
    from backend.core.risk_engine import scenario_analysis
    from backend.data.historical_extended import get_city_timeseries, get_province_timeseries

    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for scenarios"}
    out = forecast_full_pipeline(values, start_year=2010, years=years)
    baseline = out.get("ensemble", {}).get("predictions", [])
    if not baseline:
        return {"error": "no baseline predictions"}
    return scenario_analysis(baseline, starting_value=values[-1])


def _call_monte_carlo(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.risk_engine import monte_carlo_simulation
    from backend.data.historical_extended import get_city_timeseries, get_province_timeseries

    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for MC"}
    return monte_carlo_simulation(values, years=years, n_sims=500)


def _call_data_provenance(name: str) -> dict[str, Any]:
    from backend.data.historical_extended import get_city_data_provenance
    return {"city": name, "provenance": get_city_data_provenance(name)}


def _call_macro_data() -> dict[str, Any]:
    from backend.data.macro_data import MACRO_DATA
    return MACRO_DATA


def _call_list_cities() -> dict[str, Any]:
    from backend.data.historical_extended import SUPPORTED_CITIES, SUPPORTED_PROVINCES
    return {"cities": sorted(SUPPORTED_CITIES), "provinces": sorted(SUPPORTED_PROVINCES)}


# --------------------------------------------------------------------------- #
# Dispatch + 参数校验
# --------------------------------------------------------------------------- #


# 每个 tool 的必填字段(白名单)
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "get_forecast": ["scope", "name", "indicator"],
    "get_diagnostics": ["scope", "name", "indicator"],
    "get_backtest": ["scope", "name", "indicator"],
    "get_risk": ["scope", "name", "indicator"],
    "get_scenarios": ["scope", "name", "indicator"],
    "get_monte_carlo": ["scope", "name", "indicator"],
    "get_data_provenance": ["name"],
    "get_macro_data": [],
    "list_cities": [],
}

_DISPATCH = {
    "get_forecast": lambda a: _call_forecast(a["scope"], a["name"], a["indicator"], a.get("years", 5)),
    "get_diagnostics": lambda a: _call_diagnostics(a["scope"], a["name"], a["indicator"]),
    "get_backtest": lambda a: _call_backtest(a["scope"], a["name"], a["indicator"]),
    "get_risk": lambda a: _call_risk(a["scope"], a["name"], a["indicator"]),
    "get_scenarios": lambda a: _call_scenarios(a["scope"], a["name"], a["indicator"], a.get("years", 5)),
    "get_monte_carlo": lambda a: _call_monte_carlo(a["scope"], a["name"], a["indicator"], a.get("years", 5)),
    "get_data_provenance": lambda a: _call_data_provenance(a["name"]),
    "get_macro_data": lambda a: _call_macro_data(),
    "list_cities": lambda a: _call_list_cities(),
}


def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """执行一个 tool,返回 dict。错误包装为 {"error": "..."}。"""
    if name not in _DISPATCH:
        return {"error": f"Tool not found: {name}"}
    required = _REQUIRED_FIELDS[name]
    missing = [f for f in required if f not in args]
    if missing:
        return {"error": f"Missing required fields: {missing}"}
    try:
        return _DISPATCH[name](args)
    except Exception as e:
        logger.warning("Tool %s failed: %s", name, e)
        return {"error": f"Internal: {type(e).__name__}: {e}"}
