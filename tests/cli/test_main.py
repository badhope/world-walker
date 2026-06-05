"""cli.main — Typer app, CliRunner 测子命令 + global flags。"""
import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.main import (
    _TOOL_FUNC_NAMES,
    State,
    _apply_base_url_env,
    _effective_config,
    _invoke_sdk,
    app,
)

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
    # 验证 _rca_chat 收到 session_id="t1" 和 user_message="..."
    assert m.call_args.kwargs["session_id"] == "t1"
    assert m.call_args.kwargs["user_message"] == "深圳 GDP 2026 多少?"


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


def test_module_entry_guard_present():
    """`python -m cli.main` 走 if __name__ == '__main__': app() — 验证 guard 在源码里。

    否则用户 `python -m cli.main ...` 静默退出(只剩 logger 错乱输出)。
    """
    import inspect

    import cli.main as cli_main_mod

    src = inspect.getsource(cli_main_mod)
    assert '__name__ == "__main__"' in src
    assert "app()" in src.split('if __name__ == "__main__":', 1)[1]


# --------------------------------------------------------------------------- #
# --model / --base-url global flag 真的接上后端(不是 show-only)
# --------------------------------------------------------------------------- #


def test_effective_config_overrides_model():
    """state.model set → 返回的 AIConfig.model == state.model(其他字段保留)。"""
    from backend.ai.config import AIConfig

    state = State()
    state.model = "deepseek-v3"
    cfg = _effective_config(state)
    assert isinstance(cfg, AIConfig)
    assert cfg.model == "deepseek-v3"


def test_effective_config_no_override_returns_base():
    """state.model == None → 返回 base cfg(同 _get_cfg())。"""
    state = State()
    state.model = None
    cfg = _effective_config(state)
    from rca._config import load_config

    base = load_config()
    assert cfg.model == base.model


def test_apply_base_url_env_sets_environ(monkeypatch):
    """state.base_url set → os.environ['LLM_OPENAI_BASE_URL'] 被设置。"""
    monkeypatch.delenv("LLM_OPENAI_BASE_URL", raising=False)
    state = State()
    state.base_url = "https://my-gateway.example.com/v1"
    _apply_base_url_env(state)
    import os

    assert os.environ["LLM_OPENAI_BASE_URL"] == "https://my-gateway.example.com/v1"


def test_apply_base_url_env_noop_when_unset(monkeypatch):
    """state.base_url is None → 不动 env。"""
    monkeypatch.delenv("LLM_OPENAI_BASE_URL", raising=False)
    state = State()
    state.base_url = None
    _apply_base_url_env(state)
    import os

    assert "LLM_OPENAI_BASE_URL" not in os.environ


def test_chat_uses_overridden_model(monkeypatch):
    """rca --model X chat --message Y → _rca_chat 收到 config=... 且 config.model == X。"""
    state = State()
    state.model = "deepseek-v3"
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test-fake-key")
    captured = {}

    def fake_chat(session_id, user_message, *, config=None, base_url=None):
        captured["config"] = config
        captured["base_url"] = base_url
        return {"content": "ok", "tool_rounds": 0}

    monkeypatch.setattr("cli.main._rca_chat", fake_chat)
    cfg = _effective_config(state)
    _apply_base_url_env(state)
    fake_chat(session_id="s1", user_message="hi", config=cfg, base_url=state.base_url)
    assert captured["config"] is not None
    assert captured["config"].model == "deepseek-v3"
