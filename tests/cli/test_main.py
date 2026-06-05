"""cli.main — Typer app, CliRunner 测子命令 + global flags。"""
import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch

from cli.main import app, _invoke_sdk, _TOOL_FUNC_NAMES

runner = CliRunner()


# --------------------------------------------------------------------------- #
# forecast
# --------------------------------------------------------------------------- #


def test_forecast_rich_default():
    """rca forecast --city shenzhen --indicator gdp → 含 '深圳' 'gdp'。"""
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {
                "scope": "city", "name": "深圳", "indicator": "gdp",
                "ensemble": {"predictions": [40344.36, 42273.63, 44202.90],
                             "ci_lower": [39010.57, 40591.51, 42240.15],
                             "ci_upper": [41678.14, 43955.75, 46165.65]},
                "diagnostics_verdict": "WARN", "backtest_mape": 2.35, "data_points": 16,
            },
            "navigate_to": None,
        }
        result = runner.invoke(app, ["forecast", "--city", "shenzhen", "--indicator", "gdp"])
    assert result.exit_code == 0
    assert "深圳" in result.stdout or "shenzhen" in result.stdout
    assert "gdp" in result.stdout.lower()


def test_forecast_json_output():
    """--format json → 合法 JSON, 含 'ensemble'。"""
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {"name": "深圳", "indicator": "gdp", "ensemble": {"predictions": [1, 2, 3]}},
            "navigate_to": None,
        }
        result = runner.invoke(app, ["--format", "json", "forecast", "--city", "shenzhen", "--indicator", "gdp"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert "ensemble" in parsed


def test_forecast_plain_output():
    """--format plain → key=value 行。"""
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {"name": "深圳", "indicator": "gdp", "ensemble": {"predictions": [1, 2, 3]}},
            "navigate_to": None,
        }
        result = runner.invoke(app, ["--format", "plain", "forecast", "--city", "shenzhen", "--indicator", "gdp"])
    assert result.exit_code == 0
    assert "name=深圳" in result.stdout
    assert "indicator=gdp" in result.stdout


# --------------------------------------------------------------------------- #
# diagnostics / backtest / risk
# --------------------------------------------------------------------------- #


def test_diagnostics_rich_default():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {"data": {"name": "上海", "indicator": "gdp", "verdict": "PASS"}, "navigate_to": "/x"}
        result = runner.invoke(app, ["diagnostics", "--city", "shanghai", "--indicator", "gdp"])
    assert result.exit_code == 0
    assert "上海" in result.stdout


def test_backtest_json_output():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {"data": {"name": "北京", "mape": 2.35}, "navigate_to": "/x"}
        result = runner.invoke(app, ["--format", "json", "backtest", "--city", "beijing", "--indicator", "gdp"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["mape"] == 2.35


def test_risk_rich_default():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {"name": "广州", "indicator": "gdp",
                     "var_95": {"var_pct": -3.69}, "volatility": {"annualized_volatility": 0.026}},
            "navigate_to": "/x",
        }
        result = runner.invoke(app, ["risk", "--city", "guangzhou", "--indicator", "gdp"])
    assert result.exit_code == 0
    assert "广州" in result.stdout


# --------------------------------------------------------------------------- #
# scenarios / monte-carlo
# --------------------------------------------------------------------------- #


def test_scenarios_default_years():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {"name": "深圳", "indicator": "gdp", "scenarios": {"baseline": [1, 2, 3]}},
            "navigate_to": "/x",
        }
        result = runner.invoke(app, ["scenarios", "--city", "shenzhen", "--indicator", "gdp"])
    assert result.exit_code == 0
    call_args = m.call_args[0][1]
    assert call_args["years"] == 5


def test_monte_carlo_custom_years():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {"data": {"name": "杭州", "p5": 100, "p95": 200}, "navigate_to": "/x"}
        result = runner.invoke(app, ["monte-carlo", "--city", "hangzhou", "--indicator", "gdp", "--years", "10"])
    assert result.exit_code == 0
    call_args = m.call_args[0][1]
    assert call_args["years"] == 10


# --------------------------------------------------------------------------- #
# data-provenance / macro-data / list-cities
# --------------------------------------------------------------------------- #


def test_data_provenance_rich():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {"city": "深圳", "name_en": "shenzhen", "year_range": [2010, 2025], "n_years": 16},
            "navigate_to": None,
        }
        result = runner.invoke(app, ["data-provenance", "--city", "shenzhen"])
    assert result.exit_code == 0
    assert "深圳" in result.stdout


def test_macro_data_rich():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {"year": 2025, "current": {"national_gdp": 137e12, "cpi_yoy": 1.0},
                     "yoy_pct": {"national_gdp": 4.18}},
            "navigate_to": None,
        }
        result = runner.invoke(app, ["macro-data"])
    assert result.exit_code == 0
    assert "2025" in result.stdout


def test_list_cities_rich():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {
            "data": {
                "n_cities": 10, "n_provinces": 10,
                "cities": ["深圳", "上海", "北京"],
                "provinces": ["广东", "江苏", "浙江"],
            },
            "navigate_to": None,
        }
        result = runner.invoke(app, ["list-cities"])
    assert result.exit_code == 0
    assert "10" in result.stdout
    assert "深圳" in result.stdout


def test_list_cities_plain():
    with patch("cli.main._invoke_sdk") as m:
        m.return_value = {"data": {"n_cities": 10, "cities": ["深圳"]}, "navigate_to": None}
        result = runner.invoke(app, ["--format", "plain", "list-cities"])
    assert result.exit_code == 0
    assert "n_cities=10" in result.stdout


# --------------------------------------------------------------------------- #
# chat / chat-stream
# --------------------------------------------------------------------------- #


def test_chat_message_invokes_sdk():
    """rca chat --message '...' 调 rca.chat, 渲染 content。"""
    with patch("cli.main._rca_chat") as m:
        m.return_value = {"content": "深圳 2026 GDP 预测 4.42 万亿。", "tool_rounds": 1}
        result = runner.invoke(app, ["chat", "--message", "深圳 GDP 2026 多少?", "--session", "t1"])
    assert result.exit_code == 0
    assert "4.42" in result.stdout
    m.assert_called_once_with(session_id="t1", user_message="深圳 GDP 2026 多少?")


def test_chat_stream_message_renders_events():
    """rca chat-stream --message '...' yield 多个事件, 渲染 tool_call + content。"""
    with patch("cli.main._rca_chat_stream") as m:
        m.return_value = iter([
            {"type": "thinking"},
            {"type": "tool_call", "name": "get_forecast", "args": {"city": "shenzhen"}},
            {"type": "token", "content": "深圳 "},
            {"type": "token", "content": "GDP 4.42 万亿"},
            {"type": "done", "finish_reason": "stop", "tool_rounds": 1},
        ])
        result = runner.invoke(app, ["chat-stream", "--message", "深圳 GDP"])
    # tool_call 写到 stderr;output 含 stdout+stderr 在 typer 0.12 默认
    full = result.output
    assert result.exit_code == 0
    assert "get_forecast" in full or "tool_call" in full
    assert "深圳" in result.stdout


def test_chat_no_message_exits_2():
    """rca chat 不传 --message → typer exit 2(参数错)。"""
    result = runner.invoke(app, ["chat"])
    assert result.exit_code == 2


# --------------------------------------------------------------------------- #
# global flags + dispatcher
# --------------------------------------------------------------------------- #


def test_invoke_sdk_dispatches_to_correct_function():
    """_TOOL_FUNC_NAMES 映射对 9 tool 都正确。"""
    assert _TOOL_FUNC_NAMES["get_forecast"] == "forecast"
    assert _TOOL_FUNC_NAMES["get_diagnostics"] == "diagnostics"
    assert _TOOL_FUNC_NAMES["get_backtest"] == "backtest"
    assert _TOOL_FUNC_NAMES["get_risk"] == "risk"
    assert _TOOL_FUNC_NAMES["get_scenarios"] == "scenarios"
    assert _TOOL_FUNC_NAMES["get_monte_carlo"] == "monte_carlo"
    assert _TOOL_FUNC_NAMES["get_data_provenance"] == "data_provenance"
    assert _TOOL_FUNC_NAMES["get_macro_data"] == "macro_data"
    assert _TOOL_FUNC_NAMES["get_list_cities"] == "list_cities"
    assert len(_TOOL_FUNC_NAMES) == 9


def test_help_works():
    """rca --help 不 crash。"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "rca" in result.stdout.lower() or "Regional" in result.stdout
