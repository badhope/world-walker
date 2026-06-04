def test_execute_get_forecast_success(monkeypatch):
    """get_forecast 调 investment API,返回 dict"""
    from backend.ai import tool_executor

    def fake_forecast(scope, name, indicator, years):
        return {"ensemble": {"predictions": [40100]}, "diagnostics": {"verdict": "PASS"}}

    # 用 monkeypatch 替换内部调用
    monkeypatch.setattr(tool_executor, "_call_forecast", fake_forecast)
    result = tool_executor.execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "ensemble" in result
    assert result["diagnostics"]["verdict"] == "PASS"


def test_execute_unknown_tool():
    from backend.ai import tool_executor
    result = tool_executor.execute_tool("foo", {})
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_execute_invalid_args():
    from backend.ai import tool_executor
    # get_forecast 缺 scope/name
    result = tool_executor.execute_tool("get_forecast", {"indicator": "gdp"})
    assert "error" in result
    assert "missing" in result["error"].lower() or "required" in result["error"].lower()


def test_execute_internal_error(monkeypatch):
    from backend.ai import tool_executor
    def boom(*args, **kwargs):
        raise RuntimeError("API down")
    monkeypatch.setattr(tool_executor, "_call_forecast", boom)
    result = tool_executor.execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "error" in result
    assert "API down" in result["error"]
