def test_registry_has_nine_tools():
    from backend.ai.tool_registry import list_tool_names
    names = list_tool_names()
    assert len(names) == 9
    assert set(names) == {
        "get_forecast", "get_diagnostics", "get_backtest",
        "get_risk", "get_scenarios", "get_monte_carlo",
        "get_data_provenance", "get_macro_data", "list_cities",
    }


def test_each_tool_has_required_fields():
    from backend.ai.tool_registry import TOOLS
    for tool in TOOLS:
        assert tool["type"] == "function"
        f = tool["function"]
        assert "name" in f and "description" in f and "parameters" in f
        params = f["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        # required 字段可空(get_macro_data / list_cities 无必填)
        required = params.get("required", [])
        assert isinstance(required, list)
        for r in required:
            assert r in params["properties"]


def test_indicator_enum_consistent():
    from backend.ai.tool_registry import INDICATOR_LIST
    from backend.data.historical_extended import INDICATOR_META
    # 每个 tool 用的 indicator enum 必须和数据层一致
    assert set(INDICATOR_LIST) == set(INDICATOR_META.keys())


def test_get_tool_by_name():
    import pytest
    from backend.ai.tool_registry import get_tool, TOOLS
    tool = get_tool("get_forecast")
    assert tool in TOOLS
    assert tool["function"]["name"] == "get_forecast"
    with pytest.raises(KeyError):
        get_tool("nonexistent")
