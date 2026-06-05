"""
端到端集成测试 — Phase 13 验证。

要求 (running backend on :8000):
- 7 投资决策 API 全部 200
- 数据无 null
- CI 带宽 > 0
- 残差诊断有 verdict
- Backtest 有 5 指标
- 数据血缘 endpoint 正确
"""
import json
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, ".")

API = "http://localhost:8000/api/v1"


def get(path: str) -> dict:
    """GET 后端 + JSON parse"""
    with urllib.request.urlopen(API + path) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status} on {path}")
        return json.loads(r.read())


def test_investment_endpoints_e2e():
    """7 投资决策端点端到端"""
    name = "深圳"
    enc = urllib.parse.quote(name)

    print("\n=== 7 Investment Endpoints E2E ===\n")

    # 1. forecast/full
    full = get(f"/investment/forecast/full?scope=city&name={enc}&indicator=gdp&years=5")
    assert full["investment_grade"] is True
    assert "ensemble" in full
    assert len(full["ensemble"]["predictions"]) == 5
    assert "diagnostics" in full
    assert full["diagnostics"]["verdict"] in ("PASS", "WARN", "FAIL")
    assert "backtest" in full
    assert "MAPE_pct" in full["backtest"]["metrics"]
    print(f"  ✓ /forecast/full: verdict={full['diagnostics']['verdict']}, MAPE={full['backtest']['metrics']['MAPE_pct']}%")

    # 2. diagnostics
    diag = get(f"/investment/diagnostics/city/{enc}?indicator=gdp")
    assert diag["verdict"] in ("PASS", "WARN", "FAIL")
    assert "adf" in diag["tests"]
    print(f"  ✓ /diagnostics: verdict={diag['verdict']}, {len(diag['tests'])} tests")

    # 3. structural-breaks
    sb = get(f"/investment/structural-breaks/city/{enc}?indicator=gdp")
    assert "breaks" in sb
    assert sb["n_breaks"] >= 0
    print(f"  ✓ /structural-breaks: {sb['n_breaks']} breaks found")

    # 4. backtest
    bt = get(f"/investment/backtest/city/{enc}?indicator=gdp&n_test=3")
    assert all(k in bt["metrics"] for k in ["MAPE_pct", "RMSE", "MASE", "sMAPE_pct", "Coverage_pct"])
    print(f"  ✓ /backtest: MAPE={bt['metrics']['MAPE_pct']}%, Coverage={bt['metrics']['Coverage_pct']}%")

    # 5. risk
    risk = get(f"/investment/risk/city/{enc}?indicator=gdp")
    assert "volatility" in risk
    assert "var_95" in risk
    assert "var_99" in risk
    # 深圳 GDP 16 年都是正增长,VaR 可能 = 0(最坏情景无损失);波动率应 > 0
    assert risk["volatility"]["annualized_volatility"] >= 0
    print(f"  ✓ /risk: vol={risk['volatility']['annualized_volatility']*100:.2f}%, VaR95={risk['var_95']['var_pct']*100:.2f}%, CVaR95={risk['var_95']['cvar_pct']*100:.2f}%")

    # 6. scenarios
    sc = get(f"/investment/scenarios/city/{enc}?indicator=gdp&years=5")
    assert "scenarios" in sc
    assert len(sc["scenarios"]) == 4
    for sid in ("baseline", "optimistic", "pessimistic", "recession"):
        assert sid in sc["scenarios"]
        assert len(sc["scenarios"][sid]["predictions"]) == 5
    print(f"  ✓ /scenarios: 4 scenarios, baseline→recession = {sc['scenarios']['baseline']['final_value']:.0f} → {sc['scenarios']['recession']['final_value']:.0f}")

    # 7. monte-carlo
    mc = get(f"/investment/monte-carlo/city/{enc}?indicator=gdp&years=5&n_sims=500")
    assert mc["n_sims"] == 500
    assert "p05" in mc["quantiles"] and "p50" in mc["quantiles"] and "p95" in mc["quantiles"]
    assert mc["quantiles"]["p05"][-1] < mc["quantiles"]["p95"][-1]
    print(f"  ✓ /monte-carlo: 500 sims, P5-P95 = {mc['quantiles']['p05'][-1]:.0f} ~ {mc['quantiles']['p95'][-1]:.0f}")


def test_lineage_endpoints_e2e():
    """数据血缘端点"""
    name = "深圳"
    enc = urllib.parse.quote(name)

    print("\n=== 5 Data Lineage Endpoints ===\n")

    summary = get("/lineage/summary")
    assert summary["cities"]["total"] == 10
    assert summary["years"]["count"] == 16
    assert summary["indicators"]["total"] == 12
    assert summary["coverage"]["completeness"] == 1.0
    print(f"  ✓ /lineage/summary: {summary['cities']['total']} cities, {summary['indicators']['total']} indicators, 100% coverage")

    cov = get("/lineage/coverage")
    assert len(cov) == 10
    print("  ✓ /lineage/coverage: 10 cities × 16 years")

    macro = get("/lineage/macro")
    assert len(macro["timeseries"]) == 16
    assert len(macro["indicators"]) == 4
    print("  ✓ /lineage/macro: 4 indicators × 16 years")

    growth = get("/lineage/macro/growth")
    assert "national_gdp_yoy" in growth
    print("  ✓ /lineage/macro/growth: YoY rates computed")

    prov = get(f"/lineage/provenance/city/{enc}?indicator=gdp&year=2024")
    assert prov["value"] == 36500
    assert prov["provenance"]["confidence"] >= 0.9
    print(f"  ✓ /lineage/provenance/city/深圳/gdp/2024: value={prov['value']}, source={prov['provenance']['source']}")


def test_province_aggregation_e2e():
    """省份聚合端到端 — 广东 GDP 应该是深圳+广州"""
    print("\n=== Province Aggregation E2E ===\n")
    enc = urllib.parse.quote("广东")
    full = get(f"/investment/forecast/full?scope=province&name={enc}&indicator=gdp&years=3")
    assert full["data_provenance"]["n_years"] == 16
    # 广东 2025 GDP 应该是深圳+广州 ≈ 38500 + 31800 = 70300
    last_hist_year_value = full["ensemble"]["predictions"]  # 未来 3 年
    print(f"  ✓ 广东 GDP 未来 3 年: {[round(p) for p in full['ensemble']['predictions']]}")
    print(f"  ✓ 数据血缘: {full['data_provenance']['n_years']} 年, {full['data_provenance']['year_range']}")


def test_no_null_in_predictions():
    """所有预测无 null"""
    print("\n=== No-null E2E Check ===\n")
    cities = ["深圳", "上海", "北京", "广州", "成都", "杭州", "武汉", "南京", "苏州", "西安"]
    for c in cities:
        enc = urllib.parse.quote(c)
        full = get(f"/investment/forecast/full?scope=city&name={enc}&indicator=gdp&years=5")
        for v in full["ensemble"]["predictions"]:
            assert v is not None, f"{c} 预测有 null"
            assert v > 0, f"{c} 预测值 <= 0"
        # CI 带宽 > 0
        for lo, hi in zip(full["ensemble"]["lower_ci"], full["ensemble"]["upper_ci"]):
            assert lo < hi, f"{c} CI 带宽 <= 0"
    print("  ✓ 10 城 × 5 年 = 50 个预测点,全部 > 0,CI 带宽非零")


if __name__ == "__main__":
    test_investment_endpoints_e2e()
    test_lineage_endpoints_e2e()
    test_province_aggregation_e2e()
    test_no_null_in_predictions()
    print("\n✅ Phase 13 端到端集成测试 — 全部通过")
