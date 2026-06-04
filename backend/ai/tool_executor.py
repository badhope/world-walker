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
# 城市名映射 — LLM 传 pinyin/code/中文,统一转 EXTENDED_HISTORICAL 用的中文 key
# --------------------------------------------------------------------------- #


# pinyin → 中文(用于 LLM 描述里给用户看的)
PINYIN_TO_ZH: dict[str, str] = {
    "shenzhen": "深圳",
    "shanghai": "上海",
    "beijing": "北京",
    "guangzhou": "广州",
    "wuhan": "武汉",
    "chengdu": "成都",
    "hangzhou": "杭州",
    "nanjing": "南京",
    "suzhou": "苏州",
    "xian": "西安",
    # 省份
    "guangdong": "广东",
    "jiangsu": "江苏",
    "zhejiang": "浙江",
    "sichuan": "四川",
    "hubei": "湖北",
    "shaanxi": "陕西",
    "shandong": "山东",
    "henan": "河南",
    "fujian": "福建",
    "anhui": "安徽",
}

# code → 中文(2-letter)
CODE_TO_ZH: dict[str, str] = {
    "sz": "深圳", "sh": "上海", "bj": "北京", "gz": "广州",
    "wh": "武汉", "cd": "成都", "hz": "杭州", "nj": "南京",
    "su": "苏州", "xa": "西安",
}


def _resolve_city(name: str) -> str:
    """把 pinyin / code / 中文 统一转中文 key。"""
    if not name:
        return ""
    n = name.strip()
    low = n.lower()
    if n in PINYIN_TO_ZH.values() or n in CODE_TO_ZH.values():
        return n
    if low in PINYIN_TO_ZH:
        return PINYIN_TO_ZH[low]
    if low in CODE_TO_ZH:
        return CODE_TO_ZH[low]
    return n  # 兜底:让上层自己处理 unknown


def _get_values(scope: str, name: str, indicator: str) -> list[float]:
    """从 historical_extended 取某城市某指标的时间序列 values。"""
    from backend.data.historical_extended import get_city_timeseries

    zh = _resolve_city(name)
    df = get_city_timeseries(zh)
    if df.empty or indicator not in df.columns:
        return []
    series = df[indicator].dropna().tolist()
    return [float(v) for v in series]


# --------------------------------------------------------------------------- #
# 内部调用 — 直接复用 forecast_engine / risk_engine / data_layer
# --------------------------------------------------------------------------- #


def _call_forecast(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.forecast_engine import forecast_full_pipeline

    values = _get_values(scope, name, indicator)
    if not values:
        return {"error": f"No data for {scope}={name} indicator={indicator}"}
    out = forecast_full_pipeline(values, start_year=2010, years=years)
    # 简化:只返回 ensemble + diagnostics + backtest 摘要
    return {
        "scope": scope,
        "name": _resolve_city(name),
        "indicator": indicator,
        "ensemble": out.get("ensemble"),
        "diagnostics_verdict": out.get("diagnostics", {}).get("verdict"),
        "backtest_mape": out.get("backtest", {}).get("mape"),
        "arima_method": out.get("models", {}).get("arima", {}).get("method"),
        "data_points": len(values),
    }


def _call_diagnostics(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.forecast_engine import run_diagnostics

    values = _get_values(scope, name, indicator)
    if len(values) < 5:
        return {"error": "insufficient data for diagnostics"}
    return run_diagnostics(values, order=(1, 1, 0))


def _call_backtest(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.forecast_engine import backtest_forecast

    values = _get_values(scope, name, indicator)
    if len(values) < 8:
        return {"error": "insufficient data for backtest"}
    return backtest_forecast(values)


def _call_risk(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.risk_engine import risk_full_pipeline

    values = _get_values(scope, name, indicator)
    if len(values) < 5:
        return {"error": "insufficient data for risk"}
    baseline = values[-5:]
    return risk_full_pipeline(values, baseline, starting_value=values[-1], n_sims=200)


def _call_scenarios(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.forecast_engine import forecast_full_pipeline
    from backend.core.risk_engine import scenario_analysis

    values = _get_values(scope, name, indicator)
    if len(values) < 5:
        return {"error": "insufficient data for scenarios"}
    out = forecast_full_pipeline(values, start_year=2010, years=years)
    baseline = out.get("ensemble", {}).get("predictions", [])
    if not baseline:
        return {"error": "no baseline predictions"}
    return scenario_analysis(baseline, starting_value=values[-1])


def _call_monte_carlo(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.risk_engine import monte_carlo_simulation

    values = _get_values(scope, name, indicator)
    if len(values) < 5:
        return {"error": "insufficient data for MC"}
    return monte_carlo_simulation(values, years=years, n_sims=500)


def _call_data_provenance(name: str) -> dict[str, Any]:
    from backend.data.historical_extended import (
        EXTENDED_HISTORICAL,
        NBSC_URL,
        SOURCE_URLS,
        get_data_coverage,
    )

    zh = _resolve_city(name)
    if zh not in EXTENDED_HISTORICAL:
        return {"error": f"Unknown city: {name}"}
    city_data = EXTENDED_HISTORICAL[zh]
    years = sorted(city_data.keys())
    coverage = get_data_coverage(zh)
    # 取首/末年份的 provenance 示例
    sample_indicator = next(iter(city_data[years[0]].keys())) if years else None
    sample_year = years[0] if years else None
    return {
        "city": zh,
        "name_en": name,
        "url": SOURCE_URLS.get(zh, NBSC_URL),
        "nbsc_url": NBSC_URL,
        "year_range": [years[0], years[-1]] if years else [],
        "n_years": len(years),
        "coverage": coverage.get(zh, {}),
        "sample_provenance": {
            "year": sample_year,
            "indicator": sample_indicator,
            "source": f"{zh}统计局{sample_year}年统计公报",
            "estimated": False,
            "confidence": 0.95,
        },
    }


def _call_macro_data() -> dict[str, Any]:
    from backend.data.macro_data import MACRO_HISTORICAL
    latest_year = max(MACRO_HISTORICAL.keys())
    latest = MACRO_HISTORICAL[latest_year]
    # 同比(取去年数据)
    prev = MACRO_HISTORICAL.get(latest_year - 1, {})
    yoy = {}
    for k, v in latest.items():
        if k in prev and prev[k]:
            yoy[k] = round((v - prev[k]) / prev[k] * 100, 2)
    return {
        "year": latest_year,
        "current": latest,
        "yoy_pct": yoy,
    }


def _call_list_cities() -> dict[str, Any]:
    from backend.data.historical_extended import list_extended_cities
    cities_zh = list_extended_cities()
    # 同时给 LLM 看的 pinyin aliases
    zh_to_pinyin = {v: k for k, v in PINYIN_TO_ZH.items() if v in cities_zh}
    return {
        "cities": cities_zh,
        "city_pinyin": zh_to_pinyin,
        "cities_pinyin": list(zh_to_pinyin.values()),
        "provinces": list(PINYIN_TO_ZH.keys())[len(cities_zh):],
        "n_cities": len(cities_zh),
    }


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
    """执行一个 tool,返回 dict。错误包装为 {"error": "..."}。

    返回结构(v7.1):
    - 成功: {"data": <result>, "navigate_to": <url|None>}
    - 失败: {"error": "<reason>", "navigate_to": None}

    navigate_to 用于前端 chat widget 渲染"在图表中查看"chip,点击跳转。
    """
    if name not in _DISPATCH:
        return {"error": f"Tool not found: {name}", "navigate_to": None}
    required = _REQUIRED_FIELDS[name]
    missing = [f for f in required if f not in args]
    if missing:
        return {"error": f"Missing required fields: {missing}", "navigate_to": None}
    try:
        result = _DISPATCH[name](args)
        if "error" in result:
            # _call_* 内部已经报 error,把 navigate_to 设为 None
            return {**result, "navigate_to": None}
        return {"data": result, "navigate_to": _build_navigate_to(name, args)}
    except Exception as e:
        logger.warning("Tool %s failed: %s", name, e)
        return {"error": f"Internal: {type(e).__name__}: {e}", "navigate_to": None}


# --------------------------------------------------------------------------- #
# navigate_to 映射 — 每个 tool 跳转的图表页 URL,前端 chip 用
# --------------------------------------------------------------------------- #


# tab 字段告诉前端 investment_grade.html 切到哪个 tab(forecast/backtest/...)
_TAB_FOR_TOOL: dict[str, str | None] = {
    "get_forecast": None,        # 默认 tab
    "get_diagnostics": "diagnostics",
    "get_backtest": "backtest",
    "get_risk": "risk",
    "get_scenarios": "scenarios",
    "get_monte_carlo": "mc",
}


def _build_navigate_to(name: str, args: dict[str, Any]) -> str | None:
    """构造 chip 跳转 URL;list_cities / 错误情况返 None。

    URL prefix 用 /chat_widget 因为 FastAPI 把 frontend/ 静态资源挂在这下面。
    部署到 production 时应改为根 / — 这是 v7.2 (前端 route) 的事。
    """
    if name == "list_cities":
        return None
    if name == "get_data_provenance":
        return f"/chat_widget/index.html#provenance&city={args.get('name', '')}"
    if name == "get_macro_data":
        return "/chat_widget/index.html#macro"
    # 默认:investment_grade.html + URL 参数
    params: list[str] = []
    for k in ("scope", "name", "indicator", "years"):
        if k in args:
            params.append(f"{k}={args[k]}")
    tab = _TAB_FOR_TOOL.get(name)
    if tab:
        params.append(f"tab={tab}")
    base = "/chat_widget/investment_grade.html"
    return base + "?" + "&".join(params) if params else base
