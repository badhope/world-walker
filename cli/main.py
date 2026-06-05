"""Typer CLI 入口 — 11 个子命令 + global --format / --model / --base-url / --no-color。

设计:
- rca 是主命令(Typer app)
- 9 tool 子命令: forecast / diagnostics / backtest / risk / scenarios / monte-carlo /
  data-provenance / macro-data / list-cities
- 2 chat 子命令: chat / chat-stream
- global --format {rich,json,plain} (默认 rich)
- global --model X 覆盖 LLM
- global --base-url X 覆盖 gateway
- 错误处理: RCAError → exit 1; LLM 错 → exit 3
"""
from __future__ import annotations

import typer

from cli import formatters
from cli._resolve import (
    build_backtest_args,
    build_data_provenance_args,
    build_diagnostics_args,
    build_forecast_args,
    build_list_cities_args,
    build_macro_data_args,
    build_monte_carlo_args,
    build_risk_args,
    build_scenarios_args,
)
from rca import tools as _rca_tools
from rca.chat import chat as _rca_chat
from rca.chat import chat_stream as _rca_chat_stream
from rca.errors import (
    LLMUnavailableError,
    RCAError,
    ToolArgumentError,
    ToolNotFoundError,
)

app = typer.Typer(
    name="rca",
    help="Regional Economic Analysis agent — CLI for 9 tools + LLM chat.",
    no_args_is_help=True,
    add_completion=False,
)

# --------------------------------------------------------------------------- #
# global state — 用 typer.Context 透传
# --------------------------------------------------------------------------- #


class State:
    format: str = "rich"
    model: str | None = None
    base_url: str | None = None
    no_color: bool = False


@app.callback()
def _main_callback(
    ctx: typer.Context,
    format: str = typer.Option("rich", "--format", help="Output format: rich / json / plain"),
    model: str | None = typer.Option(None, "--model", help="Override LLM model (e.g. deepseek-v3)"),
    base_url: str | None = typer.Option(None, "--base-url", help="Override LLM gateway base URL"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable rich colors"),
) -> None:
    state = State()
    state.format = format
    state.model = model
    state.base_url = base_url
    state.no_color = no_color
    ctx.obj = state


def _get_state(ctx: typer.Context) -> State:
    return ctx.obj or State()


# --------------------------------------------------------------------------- #
# SDK invoke + 错误处理
# --------------------------------------------------------------------------- #


# tool_name → rca.tools 函数名映射
_TOOL_FUNC_NAMES = {
    "get_forecast": "forecast",
    "get_diagnostics": "diagnostics",
    "get_backtest": "backtest",
    "get_risk": "risk",
    "get_scenarios": "scenarios",
    "get_monte_carlo": "monte_carlo",
    "get_data_provenance": "data_provenance",
    "get_macro_data": "macro_data",
    "get_list_cities": "list_cities",
}


def _invoke_sdk(tool_name: str, kwargs: dict) -> dict:
    """调 rca.tools 的 tool,返 {"data": ..., "navigate_to": ...}。

    错误处理: 业务错 → exit 1; LLM 错 → exit 3。
    """
    func = getattr(_rca_tools, _TOOL_FUNC_NAMES[tool_name])
    try:
        return func(**kwargs)
    except ToolNotFoundError as e:
        typer.echo(f"ERROR: {e}", err=True)
        raise typer.Exit(code=1)
    except ToolArgumentError as e:
        typer.echo(f"ERROR: {e}", err=True)
        raise typer.Exit(code=1)
    except LLMUnavailableError as e:
        typer.echo(f"ERROR: LLM unavailable: {e}", err=True)
        raise typer.Exit(code=3)


def _render(ctx: typer.Context, data: dict, command: str) -> None:
    """按 global --format 渲染。"""
    state = _get_state(ctx)
    if state.format == "json":
        typer.echo(formatters.format_json(data))
    elif state.format == "plain":
        typer.echo(formatters.format_plain(data))
    else:  # rich
        typer.echo(formatters.format_rich(data, command=command))


# --------------------------------------------------------------------------- #
# 9 tool 子命令
# --------------------------------------------------------------------------- #


@app.command()
def forecast(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city", help="城市拼音 (shenzhen) / 省份名 (guangdong)"),
    indicator: str = typer.Option(..., "--indicator", help="指标: gdp / population / ..."),
    scope: str = typer.Option("city", "--scope", help="city 或 province"),
    years: int | None = typer.Option(None, "--years", help="预测年数 (默认 5)"),
) -> None:
    """多年预测 ensemble + diagnostics + backtest 摘要。"""
    args = build_forecast_args(city=city, indicator=indicator, scope=scope, years=years)
    result = _invoke_sdk("get_forecast", args)
    _render(ctx, result["data"], command="forecast")


@app.command()
def diagnostics(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city"),
    indicator: str = typer.Option(..., "--indicator"),
    scope: str = typer.Option("city", "--scope"),
) -> None:
    """5 项残差诊断(ADF/KPSS/Ljung-Box/Jarque-Bera/Breusch-Pagan) + verdict。"""
    args = build_diagnostics_args(city=city, indicator=indicator, scope=scope)
    result = _invoke_sdk("get_diagnostics", args)
    _render(ctx, result["data"], command="diagnostics")


@app.command()
def backtest(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city"),
    indicator: str = typer.Option(..., "--indicator"),
    scope: str = typer.Option("city", "--scope"),
) -> None:
    """Walk-forward CV 5 指标 (MAPE/RMSE/MASE/sMAPE/Coverage)。"""
    args = build_backtest_args(city=city, indicator=indicator, scope=scope)
    result = _invoke_sdk("get_backtest", args)
    _render(ctx, result["data"], command="backtest")


@app.command()
def risk(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city"),
    indicator: str = typer.Option(..., "--indicator"),
    scope: str = typer.Option("city", "--scope"),
) -> None:
    """风险指标:VaR/CVaR 95/99 + GARCH(1,1) 波动率。"""
    args = build_risk_args(city=city, indicator=indicator, scope=scope)
    result = _invoke_sdk("get_risk", args)
    _render(ctx, result["data"], command="risk")


@app.command()
def scenarios(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city"),
    indicator: str = typer.Option(..., "--indicator"),
    scope: str = typer.Option("city", "--scope"),
    years: int | None = typer.Option(None, "--years", help="默认 5"),
) -> None:
    """4 档情景预测:baseline/optimistic +10%/pessimistic -10%/recession -25%。"""
    args = build_scenarios_args(city=city, indicator=indicator, scope=scope, years=years)
    result = _invoke_sdk("get_scenarios", args)
    _render(ctx, result["data"], command="scenarios")


@app.command(name="monte-carlo")
def monte_carlo(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city"),
    indicator: str = typer.Option(..., "--indicator"),
    scope: str = typer.Option("city", "--scope"),
    years: int | None = typer.Option(None, "--years", help="默认 5"),
) -> None:
    """Monte Carlo 1000 次模拟分位数 (P5/P50/P95)。"""
    args = build_monte_carlo_args(city=city, indicator=indicator, scope=scope, years=years)
    result = _invoke_sdk("get_monte_carlo", args)
    _render(ctx, result["data"], command="monte-carlo")


@app.command(name="data-provenance")
def data_provenance(
    ctx: typer.Context,
    city: str = typer.Option(..., "--city"),
) -> None:
    """数据来源信息(URL/来源/置信度/估算标记/方法学变更)。"""
    args = build_data_provenance_args(city=city)
    result = _invoke_sdk("get_data_provenance", args)
    _render(ctx, result["data"], command="data-provenance")


@app.command(name="macro-data")
def macro_data(ctx: typer.Context) -> None:
    """4 宏观协变量当前值 + 同比(national_gdp/cpi_yoy/lpr_1y/fdi_inflow)。"""
    args = build_macro_data_args()
    result = _invoke_sdk("get_macro_data", args)
    _render(ctx, result["data"], command="macro-data")


@app.command(name="list-cities")
def list_cities(ctx: typer.Context) -> None:
    """列出系统支持的所有城市和省份。"""
    args = build_list_cities_args()
    result = _invoke_sdk("get_list_cities", args)
    _render(ctx, result["data"], command="list-cities")


# --------------------------------------------------------------------------- #
# chat / chat-stream
# --------------------------------------------------------------------------- #


@app.command()
def chat(
    ctx: typer.Context,
    message: str = typer.Option(..., "--message", "-m", help="用户问题"),
    session: str = typer.Option("cli-default", "--session", "-s", help="会话 ID(保留多轮上下文)"),
) -> None:
    """单轮 LLM agent — 自然语言 → 调 tool → 返答案。"""
    state = _get_state(ctx)
    try:
        result = _rca_chat(session_id=session, user_message=message)
    except LLMUnavailableError as e:
        typer.echo(f"ERROR: LLM unavailable: {e}", err=True)
        raise typer.Exit(code=3)
    except RCAError as e:
        typer.echo(f"ERROR: {e}", err=True)
        raise typer.Exit(code=1)
    if state.format == "json":
        typer.echo(formatters.format_json(result))
    else:
        typer.echo(result.get("content", "(no content)"))
        if result.get("tool_rounds"):
            typer.echo(f"\n[tool_rounds: {result['tool_rounds']}]", err=True)


@app.command(name="chat-stream")
def chat_stream(
    ctx: typer.Context,
    message: str = typer.Option(..., "--message", "-m", help="用户问题"),
    session: str = typer.Option("cli-default", "--session", "-s"),
) -> None:
    """流式 LLM agent — 实时显示 thinking → tool_call → token 增量。"""
    try:
        for ev in _rca_chat_stream(session_id=session, user_message=message):
            et = ev.get("type")
            if et == "thinking":
                typer.echo("[thinking]...", err=True)
            elif et == "tool_call":
                typer.echo(f"[tool_call] {ev.get('name')}({ev.get('args')})", err=True)
            elif et == "token":
                typer.echo(ev.get("content", ""), nl=False)
            elif et == "done":
                typer.echo(f"\n[done: rounds={ev.get('tool_rounds', 0)}]", err=True)
            elif et == "error":
                typer.echo(f"\n[error: {ev.get('message', '')[:200]}]", err=True)
                raise typer.Exit(code=3)
    except LLMUnavailableError as e:
        typer.echo(f"\nERROR: LLM unavailable: {e}", err=True)
        raise typer.Exit(code=3)
    except RCAError as e:
        typer.echo(f"\nERROR: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo("")


# --------------------------------------------------------------------------- #
# Module entry — 让 `python -m cli.main ...` 也能跑
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    app()
