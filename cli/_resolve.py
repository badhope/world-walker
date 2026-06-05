"""CLI args → SDK kwargs 转换桥。

设计:
- 每个 tool 1 个 builder 函数
- CLI 传 --city(用户友好)→ SDK 收 name(backend schema)
- CLI 传 --scope(默认 city)→ 直接透传
- years 默认 5
"""
from __future__ import annotations

from typing import Any


def build_forecast_args(city: str, indicator: str, scope: str = "city", years: int | None = None) -> dict[str, Any]:
    return {
        "scope": scope, "name": city, "indicator": indicator,
        "years": years if years is not None else 5,
    }


def build_diagnostics_args(city: str, indicator: str, scope: str = "city") -> dict[str, Any]:
    return {"scope": scope, "name": city, "indicator": indicator}


def build_backtest_args(city: str, indicator: str, scope: str = "city") -> dict[str, Any]:
    return {"scope": scope, "name": city, "indicator": indicator}


def build_risk_args(city: str, indicator: str, scope: str = "city") -> dict[str, Any]:
    return {"scope": scope, "name": city, "indicator": indicator}


def build_scenarios_args(city: str, indicator: str, scope: str = "city", years: int | None = None) -> dict[str, Any]:
    return {
        "scope": scope, "name": city, "indicator": indicator,
        "years": years if years is not None else 5,
    }


def build_monte_carlo_args(city: str, indicator: str, scope: str = "city", years: int | None = None) -> dict[str, Any]:
    return {
        "scope": scope, "name": city, "indicator": indicator,
        "years": years if years is not None else 5,
    }


def build_data_provenance_args(city: str) -> dict[str, Any]:
    return {"name": city}


def build_macro_data_args() -> dict[str, Any]:
    return {}


def build_list_cities_args() -> dict[str, Any]:
    return {}
