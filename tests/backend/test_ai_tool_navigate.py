"""tool_executor 给 9 个 tool 注入 navigate_to URL,前端可跳转图表页。"""


def test_forecast_navigate_to_investment_grade():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "navigate_to" in out
    assert out["navigate_to"] == "/chat_widget/investment_grade.html?scope=city&name=shenzhen&indicator=gdp&years=3"


def test_diagnostics_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_diagnostics", {"scope": "city", "name": "shanghai", "indicator": "gdp"})
    assert "navigate_to" in out
    assert "tab=diagnostics" in out["navigate_to"]


def test_backtest_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_backtest", {"scope": "city", "name": "shenzhen", "indicator": "gdp"})
    assert "tab=backtest" in out["navigate_to"]


def test_risk_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_risk", {"scope": "city", "name": "shenzhen", "indicator": "gdp"})
    assert "tab=risk" in out["navigate_to"]


def test_scenarios_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_scenarios", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "tab=scenarios" in out["navigate_to"]


def test_monte_carlo_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_monte_carlo", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "tab=mc" in out["navigate_to"]


def test_data_provenance_navigate_to_index():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_data_provenance", {"name": "shenzhen"})
    assert out["navigate_to"] == "/chat_widget/index.html#provenance&city=shenzhen"


def test_macro_data_navigate_to_index():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_macro_data", {})
    assert out["navigate_to"] == "/chat_widget/index.html#macro"


def test_list_cities_no_navigate_to():
    """list_cities 纯文本,无跳转。"""
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("list_cities", {})
    assert out.get("navigate_to") is None


def test_navigate_to_url_uses_pinyin_resolved_name():
    """name 是 pinyin,URL 里也用 pinyin(前端 investment_grade.html 接受 pinyin query)。"""
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    # name 保持原样(pinyin),前端 investment_grade 会转
    assert "name=shenzhen" in out["navigate_to"]


def test_unknown_tool_returns_error_with_null_navigate():
    """不存在的 tool → error + navigate_to None。"""
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("nuke_city", {"name": "shenzhen"})
    assert "error" in out
    assert out.get("navigate_to") is None


def test_missing_fields_returns_error_with_null_navigate():
    """缺必填字段 → error + navigate_to None。"""
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_forecast", {"scope": "city", "name": "shenzhen"})
    assert "error" in out
    assert out.get("navigate_to") is None
