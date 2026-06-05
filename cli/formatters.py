"""3 output formatters for CLI:
- format_json: machine-readable JSON
- format_plain: key=value,一行一对
- format_rich: 用 rich.Table 渲染人类可读

设计:
- 每个 formatter 接受 data dict,返 str(rich 返 Console capture)
- 不做 ANSI escape 检测 — 那是终端的事
"""
from __future__ import annotations

import io
import json
from typing import Any


def _flatten(data: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    """递归展开嵌套 dict 成 (key.path, value) 列表。"""
    out = []
    for k, v in data.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.extend(_flatten(v, prefix=key))
        elif isinstance(v, list):
            out.append((key, "[" + ", ".join(str(x) for x in v) + "]"))
        else:
            out.append((key, v))
    return out


def format_json(data: dict[str, Any]) -> str:
    """JSON formatter — 完整 dict,ensure_ascii=False 保中文。"""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def format_plain(data: dict[str, Any]) -> str:
    """Plain formatter — key=value 行, 嵌套 dict 用 .join。

    例:
        scope=city
        name=深圳
        ensemble.predictions=[40344.36, 42273.63, 44202.90]
    """
    lines = []
    for k, v in _flatten(data):
        lines.append(f"{k}={v}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Rich formatter — 6 命令特定 table 渲染
# --------------------------------------------------------------------------- #


def format_rich(data: dict[str, Any], command: str) -> str:
    """Rich formatter — 用 rich.Table 渲染,返 str(用 Console capture)。

    不用 rich.Live 不用 rich.Panel — 简单 Table。
    命令特定:
    - forecast: ensemble.predictions + CI + diagnostics
    - list-cities: 城市/省份两行
    - risk: VaR / CVaR / Vol
    - data-provenance: 字段表
    - macro-data: 指标 + 当前值 + YoY
    - 其他: 嵌套 key=value 表
    """
    from rich.console import Console

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False, width=120, legacy_windows=False, record=True)

    if command == "forecast" and "ensemble" in data:
        _render_forecast_table(console, data)
    elif command == "list-cities" and "cities" in data:
        _render_cities_table(console, data)
    elif command == "risk" and "var_95" in data:
        _render_risk_table(console, data)
    elif command == "data-provenance" and "city" in data:
        _render_provenance_table(console, data)
    elif command == "macro-data" and "current" in data:
        _render_macro_table(console, data)
    else:
        _render_generic_kv(console, data, title=command)

    return console.export_text(styles=False)


def _render_forecast_table(console, data: dict) -> None:
    from rich.table import Table
    t = Table(title=f"{data.get('name', '?')} {data.get('indicator', '?').upper()} Forecast ({data.get('years', '?')}y)", show_header=True)
    t.add_column("Year", style="cyan")
    t.add_column("Prediction", justify="right", style="green")
    t.add_column("95% CI", justify="right")
    ensemble = data.get("ensemble", {}) or {}
    preds = ensemble.get("predictions", [])
    ci_lower = ensemble.get("ci_lower", [])
    ci_upper = ensemble.get("ci_upper", [])
    for i, p in enumerate(preds):
        ci = f"[{ci_lower[i]:.2f}, {ci_upper[i]:.2f}]" if i < len(ci_lower) and i < len(ci_upper) else "-"
        t.add_row(str(2024 + i), f"{p:,.2f}", ci)
    console.print(t)
    if data.get("diagnostics_verdict"):
        console.print(f"Diagnostics: {data['diagnostics_verdict']}")
    if data.get("backtest_mape") is not None:
        console.print(f"Backtest MAPE: {data['backtest_mape']:.2f}%")
    if data.get("data_points"):
        console.print(f"Data points: {data['data_points']}")


def _render_cities_table(console, data: dict) -> None:
    from rich.table import Table
    t = Table(title=f"Supported Cities & Provinces ({data.get('n_cities', '?')} cities)", show_header=True)
    t.add_column("Cities", style="cyan")
    t.add_column("Provinces", style="magenta")
    cities = data.get("cities", [])
    provinces = data.get("provinces", [])
    n = max(len(cities), len(provinces))
    for i in range(n):
        c = cities[i] if i < len(cities) else ""
        p = provinces[i] if i < len(provinces) else ""
        t.add_row(c, p)
    console.print(t)


def _render_risk_table(console, data: dict) -> None:
    from rich.table import Table
    t = Table(title=f"{data.get('name', '?')} {data.get('indicator', '?').upper()} Risk", show_header=True)
    t.add_column("Metric", style="cyan")
    t.add_column("Value", justify="right", style="green")
    if "var_95" in data and isinstance(data["var_95"], dict):
        t.add_row("VaR 95%", f"{data['var_95'].get('var_pct', 0):.2f}%")
    if "volatility" in data and isinstance(data["volatility"], dict):
        vol = data["volatility"].get("annualized_volatility", 0)
        t.add_row("Annualized Vol", f"{vol * 100:.2f}%")
    if "cvar_95" in data and isinstance(data["cvar_95"], dict):
        t.add_row("CVaR 95%", f"{data['cvar_95'].get('cvar_pct', 0):.2f}%")
    console.print(t)


def _render_provenance_table(console, data: dict) -> None:
    from rich.table import Table
    t = Table(title=f"Data Provenance: {data.get('city', '?')}", show_header=True)
    t.add_column("Field", style="cyan")
    t.add_column("Value")
    for k, v in data.items():
        if isinstance(v, (str, int, float)):
            t.add_row(k, str(v))
    console.print(t)


def _render_macro_table(console, data: dict) -> None:
    from rich.table import Table
    t = Table(title=f"Macro Data ({data.get('year', '?')})", show_header=True)
    t.add_column("Indicator", style="cyan")
    t.add_column("Value", justify="right", style="green")
    t.add_column("YoY %", justify="right")
    cur = data.get("current", {}) or {}
    yoy = data.get("yoy_pct", {}) or {}
    for k, v in cur.items():
        yoy_v = yoy.get(k)
        t.add_row(k, f"{v:,.2f}" if isinstance(v, (int, float)) else str(v), f"{yoy_v:+.2f}%" if yoy_v is not None else "-")
    console.print(t)


def _render_generic_kv(console, data: dict, title: str) -> None:
    from rich.table import Table
    t = Table(title=title, show_header=True)
    t.add_column("Key", style="cyan")
    t.add_column("Value")
    for k, v in _flatten(data):
        t.add_row(k, str(v))
    console.print(t)
