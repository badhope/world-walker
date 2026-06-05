"""
Phase 3: 数据血缘 + provenance API
"""
import sys

sys.path.insert(0, ".")

from backend.data.historical_extended import (
    EXTENDED_HISTORICAL,
    NBSC_URL,
    SOURCE_URLS,
    get_city_indicator,
    get_data_coverage,
    list_extended_cities,
    list_extended_indicators,
)
from backend.data.historical_extended import (
    INDICATOR_META as CITY_META,
)
from backend.data.macro_data import (
    INDICATOR_META as MACRO_META,
)
from backend.data.macro_data import (
    MACRO_HISTORICAL,
    get_macro_value,
    list_macro_indicators,
)


def test_macro_data_basic():
    from backend.data.macro_data import (
        compute_growth_rates,
        get_macro_timeseries,
    )
    assert len(MACRO_HISTORICAL) == 16
    df = get_macro_timeseries()
    assert df.shape == (16, 5)
    info = get_macro_value("national_gdp", 2024)
    assert info["value"] == 1315000
    assert info["provenance"]["estimated"] is True  # 2024 是初步核算
    info2020 = get_macro_value("national_gdp", 2020)
    assert info2020["provenance"]["estimated"] is False
    growth = compute_growth_rates()
    assert "national_gdp_yoy" in growth.columns
    print("✓ Macro: 4 indicators × 16 years")
    print("✓ 2024+ 标记为 estimated (初步核算)")


def test_data_provenance_endpoint_simulation():
    """模拟 GET /data/provenance/{city}/{indicator}/{year} 的响应"""
    response = get_city_indicator("深圳", "gdp", 2024)
    assert response is not None
    assert response["value"] == 36500
    assert response["provenance"]["source"] == "深圳统计局2024年统计公报"
    assert response["provenance"]["url"].startswith("http")
    assert response["provenance"]["estimated"] is False
    assert response["provenance"]["confidence"] == 0.95
    print(f"✓ /data/provenance 深圳/gdp/2024 → {response['provenance']['source']}")


def test_coverage_report():
    cov = get_data_coverage()
    total_cells = 0
    total_filled = 0
    for city, info in cov.items():
        assert info["completeness"] == 1.0
        assert info["year_count"] == 16
        total_cells += 16 * 12
        total_filled += int(16 * 12 * info["completeness"])
    print(f"✓ Coverage: 10 城 × 16 年 × 12 指标 = {total_cells} cells, {total_filled} filled (100%)")


if __name__ == "__main__":
    test_macro_data_basic()
    test_data_provenance_endpoint_simulation()
    test_coverage_report()
    print("\n✅ Phase 2+3 测试全部通过")
