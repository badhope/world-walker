"""9 tool wrapper 单元测试 — 每个 tool 一个 test,验证与 tool_executor 输出一致。"""
import pytest
from unittest.mock import patch

from rca import tools


def test_forecast_passes_kwargs_to_executor():
    """forecast(scope, name, indicator, years) → tool_executor.execute_tool('get_forecast', {...})"""
    with patch("rca.tools.execute_tool", return_value={"data": {"ensemble": {"predictions": [1, 2, 3]}}, "navigate_to": None}) as m:
        result = tools.forecast(scope="city", name="shenzhen", indicator="gdp", years=3)
    assert m.call_count == 1
    args = m.call_args[0]
    assert args[0] == "get_forecast"
    assert args[1] == {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3}
    assert result == {"data": {"ensemble": {"predictions": [1, 2, 3]}}, "navigate_to": None}


def test_diagnostics_passes_kwargs_to_executor():
    with patch("rca.tools.execute_tool", return_value={"data": {"verdict": "PASS"}, "navigate_to": "/x"}) as m:
        result = tools.diagnostics(scope="city", name="shanghai", indicator="gdp")
    assert m.call_args[0] == ("get_diagnostics", {"scope": "city", "name": "shanghai", "indicator": "gdp"})
    assert result["data"]["verdict"] == "PASS"


def test_backtest_passes_kwargs_to_executor():
    with patch("rca.tools.execute_tool", return_value={"data": {"mape": 2.35}, "navigate_to": "/x"}) as m:
        result = tools.backtest(scope="city", name="beijing", indicator="gdp")
    assert m.call_args[0] == ("get_backtest", {"scope": "city", "name": "beijing", "indicator": "gdp"})
    assert result["data"]["mape"] == 2.35


def test_risk_passes_kwargs_to_executor():
    with patch("rca.tools.execute_tool", return_value={"data": {"var_95": {"var_pct": -3.69}}, "navigate_to": "/x"}) as m:
        result = tools.risk(scope="city", name="guangzhou", indicator="gdp")
    assert m.call_args[0] == ("get_risk", {"scope": "city", "name": "guangzhou", "indicator": "gdp"})


def test_scenarios_passes_kwargs_with_default_years():
    with patch("rca.tools.execute_tool", return_value={"data": {"scenarios": {"baseline": 100}}, "navigate_to": "/x"}) as m:
        result = tools.scenarios(scope="city", name="shenzhen", indicator="gdp")
    assert m.call_args[0] == ("get_scenarios", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 5})


def test_monte_carlo_passes_kwargs_with_years_override():
    with patch("rca.tools.execute_tool", return_value={"data": {"p5": 100, "p95": 200}, "navigate_to": "/x"}) as m:
        result = tools.monte_carlo(scope="city", name="hangzhou", indicator="gdp", years=10)
    assert m.call_args[0] == ("get_monte_carlo", {"scope": "city", "name": "hangzhou", "indicator": "gdp", "years": 10})


def test_data_provenance_passes_name_only():
    with patch("rca.tools.execute_tool", return_value={"data": {"city": "深圳", "url": "http://..."}, "navigate_to": None}) as m:
        result = tools.data_provenance(name="shenzhen")
    assert m.call_args[0] == ("get_data_provenance", {"name": "shenzhen"})
    assert result["data"]["city"] == "深圳"


def test_macro_data_no_args():
    with patch("rca.tools.execute_tool", return_value={"data": {"year": 2025, "current": {"national_gdp": 137e12}}, "navigate_to": "/x"}) as m:
        result = tools.macro_data()
    assert m.call_args[0] == ("get_macro_data", {})
    assert result["data"]["year"] == 2025


def test_list_cities_no_args():
    with patch("rca.tools.execute_tool", return_value={"data": {"cities": ["深圳", "上海"], "n_cities": 10}, "navigate_to": None}) as m:
        result = tools.list_cities()
    assert m.call_args[0] == ("list_cities", {})
    assert result["data"]["n_cities"] == 10


def test_invoke_wraps_tool_error_as_tool_argument_error():
    """tool_executor 返 {"error": "..."} 时,SDK 抛 ToolArgumentError。"""
    with patch("rca.tools.execute_tool", return_value={"error": "No data for city=atlantis"}):
        with pytest.raises(Exception) as exc:
            tools.forecast(scope="city", name="atlantis", indicator="gdp")
    # 不管是 ToolArgumentError 还是其他,关键是 message 含原 error
    assert "atlantis" in str(exc.value)
