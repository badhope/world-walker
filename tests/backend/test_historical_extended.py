"""
投资决策级扩展数据测试
"""
import sys

sys.path.insert(0, ".")


def test_extended_data_basic():
    from backend.data.historical_extended import (
        EXTENDED_HISTORICAL,
        INDICATOR_META,
        get_city_indicator,
        get_city_timeseries,
        get_data_coverage,
    )

    # 1. 10 城覆盖
    assert len(EXTENDED_HISTORICAL) == 10, f"期望 10 城,实际 {len(EXTENDED_HISTORICAL)}"

    # 2. 每城 16 年
    for city, data in EXTENDED_HISTORICAL.items():
        assert len(data) == 16, f"{city} 期望 16 年,实际 {len(data)}"
        years = sorted(data.keys())
        assert years[0] == 2010, f"{city} 起始年不是 2010"
        assert years[-1] == 2025, f"{city} 结束年不是 2025"

    # 3. 每城每年 12 指标
    for city, data in EXTENDED_HISTORICAL.items():
        for year, ind in data.items():
            assert len(ind) == 12, f"{city}/{year} 期望 12 指标,实际 {len(ind)}"
            for k in INDICATOR_META.keys():
                assert k in ind, f"{city}/{year} 缺 {k}"

    # 4. get_city_timeseries
    df = get_city_timeseries("深圳")
    assert df.shape == (16, 13), f"深圳期望 (16, 13),实际 {df.shape}"
    assert "year" in df.columns
    assert "gdp" in df.columns

    # 5. get_city_indicator
    info = get_city_indicator("深圳", "gdp", 2024)
    assert info is not None
    assert info["value"] == 36500
    assert "provenance" in info
    assert info["provenance"]["estimated"] is False
    assert info["provenance"]["confidence"] >= 0.9

    # 6. coverage report
    cov = get_data_coverage()
    for city, info in cov.items():
        assert info["year_count"] == 16
        assert info["completeness"] == 1.0, f"{city} 完整性 {info['completeness']}"

    print("✓ All 12 indicators × 16 years × 10 cities — 1920 data points covered")
    print("✓ Completeness: 100%")
    print("✓ Provenance metadata: present")


def test_gdp_values_sanity():
    """GDP 数据合理性:不能倒退,数值合理范围"""
    from backend.data.historical_extended import get_city_timeseries

    for city in get_city_timeseries.__module__ and __import__(
        "backend.data.historical_extended", fromlist=["EXTENDED_HISTORICAL"]
    ).EXTENDED_HISTORICAL.keys():
        df = get_city_timeseries(city)
        gdp = df["gdp"].tolist()
        # 1. 不能倒退超过 5%(容差:疫情 2020 期间)
        for i in range(1, len(gdp)):
            pct = (gdp[i] - gdp[i - 1]) / gdp[i - 1] * 100
            # 武汉 2020 是个特殊点 (-3.8%), 允许
            if city == "武汉" and i == 10:
                assert pct < 0, "武汉 2020 应该是负增长"
                assert pct > -10, "武汉 2020 跌幅应 < 10%"
            else:
                assert pct > -5, f"{city} 第 {i} 年(20{10+i-1})GDP 跌幅过大: {pct:.1f}%"
                assert pct < 30, f"{city} 第 {i} 年 GDP 涨幅过大: {pct:.1f}%"

    print("✓ GDP 数据合理性检查通过(可容许疫情 2020 特殊点)")


def test_population_methodology_change():
    """深圳 2020 人口口径变更标注"""
    from backend.data.historical_extended import get_city_indicator

    # 2019 (常住) vs 2020 (实际管理): 数值跳跃应有 methodology_change 标注
    info_2020 = get_city_indicator("深圳", "population", 2020)
    info_2019 = get_city_indicator("深圳", "population", 2019)

    # 2020 数值应明显大于 2019 (口径变更)
    assert info_2020["value"] > info_2019["value"] * 1.2, "深圳 2020 人口未体现口径变更"
    # 应有 methodology_change 标注
    assert info_2020["provenance"]["methodology_change"] is not None

    print(f"✓ 口径变更标注:2019={info_2019['value']}万 → 2020={info_2020['value']}万(实际管理)")


if __name__ == "__main__":
    test_extended_data_basic()
    test_gdp_values_sanity()
    test_population_methodology_change()
    print("\n✅ Phase 1 数据补全测试全部通过")
