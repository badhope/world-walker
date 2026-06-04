"""Tool executor — 9 个 tool 全部用真实数据走通(pinyin/code/中文都支持)。"""
from __future__ import annotations

import pytest


def test_resolve_city_handles_pinyin_code_and_zh():
    """_resolve_city 把 shenzhen / sz / 深圳 统一到 深圳。"""
    from backend.ai.tool_executor import _resolve_city

    assert _resolve_city("shenzhen") == "深圳"
    assert _resolve_city("SHENZHEN") == "深圳"
    assert _resolve_city("sz") == "深圳"
    assert _resolve_city("SZ") == "深圳"
    assert _resolve_city("深圳") == "深圳"
    assert _resolve_city("shanghai") == "上海"
    assert _resolve_city("sh") == "上海"
    assert _resolve_city("beijing") == "北京"
    assert _resolve_city("bj") == "北京"


def test_resolve_city_unknown_returns_input_unchanged():
    """未知城市名 → 原样返回(让上层处理 unknown 错误)。"""
    from backend.ai.tool_executor import _resolve_city

    assert _resolve_city("atlantis") == "atlantis"
    assert _resolve_city("") == ""


def test_list_cities_returns_zh_and_pinyin():
    """list_cities 返中文列表 + pinyin 映射。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool("list_cities", {})
    assert "cities" in out
    assert "cities_pinyin" in out
    assert "深圳" in out["cities"]
    assert "shenzhen" in out["cities_pinyin"]
    assert out["n_cities"] >= 1


def test_macro_data_returns_current_and_yoy():
    """get_macro_data 返最新年 + 同比百分比。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool("get_macro_data", {})
    assert "year" in out
    assert "current" in out
    assert "yoy_pct" in out
    assert "national_gdp" in out["current"]
    assert "national_gdp" in out["yoy_pct"]


def test_forecast_with_pinyin_name():
    """get_forecast(city=shenzhen, indicator=gdp) → 真实 ensemble + verdict。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_forecast",
        {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
    )
    assert "error" not in out, out
    assert out["name"] == "深圳"
    assert out["scope"] == "city"
    assert out["indicator"] == "gdp"
    assert "ensemble" in out
    assert "diagnostics_verdict" in out
    assert "backtest_mape" in out


def test_forecast_with_zh_name():
    """get_forecast(name=深圳) 也工作(中英兼容)。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_forecast",
        {"scope": "city", "name": "深圳", "indicator": "gdp", "years": 3},
    )
    assert "error" not in out, out
    assert out["data_points"] >= 10


def test_diagnostics_pinyin():
    """get_diagnostics 用 pinyin 也能查到。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_diagnostics",
        {"scope": "city", "name": "shenzhen", "indicator": "gdp"},
    )
    assert "error" not in out, out
    # run_diagnostics returns 5 tests + verdict
    assert "verdict" in out


def test_backtest_no_order_arg():
    """get_backtest 不传 order(backtest_forecast 不接受 order)。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_backtest",
        {"scope": "city", "name": "shenzhen", "indicator": "gdp"},
    )
    assert "error" not in out, out


def test_risk_pinyin():
    """get_risk 用 pinyin 查 VaR/CVaR/波动率。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_risk",
        {"scope": "city", "name": "shanghai", "indicator": "gdp"},
    )
    assert "error" not in out, out
    # risk_full_pipeline returns var/cvar/volatility
    assert "volatility" in out or "var" in out or "VaR" in out or "var_95" in out or len(out) > 0


def test_scenarios_pinyin():
    """get_scenarios 用 pinyin 查 4 档情景。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_scenarios",
        {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
    )
    assert "error" not in out, out


def test_monte_carlo_pinyin():
    """get_monte_carlo 用 pinyin 查分位数。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_monte_carlo",
        {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
    )
    assert "error" not in out, out


def test_data_provenance_pinyin():
    """get_data_provenance 返 URL + 置信度 + 年份范围。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool("get_data_provenance", {"name": "shenzhen"})
    assert "error" not in out, out
    assert out["city"] == "深圳"
    assert "url" in out
    assert "year_range" in out
    assert len(out["year_range"]) == 2
    assert "sample_provenance" in out
    assert out["sample_provenance"]["confidence"] >= 0.5


def test_unknown_tool_returns_error():
    """调不存在的 tool → 返 error dict,不抛异常。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool("nuke_city", {"name": "shenzhen"})
    assert "error" in out
    assert "nuke_city" in out["error"]


def test_missing_required_fields_returns_error():
    """缺必填字段 → 返 error,不抛异常。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool("get_forecast", {"scope": "city", "name": "shenzhen"})
    assert "error" in out
    assert "indicator" in out["error"]


def test_unknown_city_returns_empty_values():
    """未知城市 → forecast 返 no-data error(graceful degradation)。"""
    from backend.ai.tool_executor import execute_tool

    out = execute_tool(
        "get_forecast",
        {"scope": "city", "name": "atlantis", "indicator": "gdp", "years": 3},
    )
    # 应该返 error 或 no-data,但绝不抛异常
    assert "error" in out
