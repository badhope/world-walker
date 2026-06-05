"""3 formatter 单元测试 — rich / json / plain。"""
import json

from cli.formatters import format_json, format_plain, format_rich


def test_format_json_returns_valid_json():
    data = {"scope": "city", "name": "shenzhen", "predictions": [1, 2, 3]}
    out = format_json(data)
    parsed = json.loads(out)
    assert parsed == data


def test_format_json_preserves_chinese():
    data = {"city": "深圳", "value": 1234}
    out = format_json(data)
    assert "深圳" in out  # ensure_ascii=False


def test_format_plain_forecast_kv_pairs():
    data = {"scope": "city", "name": "深圳", "indicator": "gdp", "data_points": 16}
    out = format_plain(data)
    for k, v in data.items():
        assert f"{k}={v}" in out


def test_format_rich_forecast_contains_table():
    """forecast 输出含 '深圳' 'gdp' + 预测数字。"""
    data = {
        "scope": "city", "name": "深圳", "indicator": "gdp", "years": 3,
        "ensemble": {"predictions": [40344.36, 42273.63, 44202.90],
                     "ci_lower": [39010.57, 40591.51, 42240.15],
                     "ci_upper": [41678.14, 43955.75, 46165.65]},
        "diagnostics_verdict": "WARN",
        "backtest_mape": 2.35,
        "data_points": 16,
    }
    out = format_rich(data, command="forecast")
    assert "深圳" in out
    assert "gdp" in out.lower()
    assert "40,344" in out or "40344" in out


def test_format_rich_list_cities_contains_count():
    """list-cities 输出含 n_cities + 城市名。"""
    data = {
        "n_cities": 10, "n_provinces": 10,
        "cities": ["深圳", "上海", "北京"],
        "provinces": ["广东", "江苏", "浙江"],
    }
    out = format_rich(data, command="list-cities")
    assert "10" in out
    assert "深圳" in out


def test_format_rich_risk_table():
    """risk 输出含 VaR 95% + 城市名。"""
    data = {
        "name": "广州", "indicator": "gdp",
        "var_95": {"var_pct": -3.69},
        "volatility": {"annualized_volatility": 0.026},
    }
    out = format_rich(data, command="risk")
    assert "广州" in out
    assert "-3.69" in out or "3.69" in out


def test_format_rich_macro_table():
    """macro-data 输出含 year + 指标名。"""
    data = {
        "year": 2025,
        "current": {"national_gdp": 137e12, "cpi_yoy": 1.0},
        "yoy_pct": {"national_gdp": 4.18, "cpi_yoy": 0.5},
    }
    out = format_rich(data, command="macro-data")
    assert "2025" in out
    assert "national_gdp" in out


def test_format_rich_provenance_table():
    """data-provenance 输出含城市 + URL 等字段。"""
    data = {
        "city": "深圳", "name_en": "shenzhen",
        "year_range": [2010, 2025], "n_years": 16,
        "primary_source": "Shenzhen Statistical Bureau",
    }
    out = format_rich(data, command="data-provenance")
    assert "深圳" in out


def test_format_rich_generic_kv():
    """未知命令 → 通用 key=value 表。"""
    data = {"foo": "bar", "n": 42}
    out = format_rich(data, command="unknown-cmd")
    assert "foo" in out
    assert "bar" in out
