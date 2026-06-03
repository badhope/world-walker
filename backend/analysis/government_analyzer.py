"""
政府端分析器 - 面向政府的区域产业经济分析
基于真实城市数据和统计分位数基准计算评分
"""

import logging
from typing import Any

from backend.analysis.base_analyzer import BaseAnalyzer
from backend.data.city_data import (
    get_all_cities,
    get_city_data,
    get_data_source_info,
)

logger = logging.getLogger(__name__)

GOV_BENCHMARKS = {
    "deficit_rate": {"low": 2.0, "medium": 3.5, "high": 5.0},
    "fiscal_self_sufficiency": {"low": 50.0, "medium": 70.0, "high": 85.0},
    "funding_efficiency": {"low": 0.6, "medium": 0.8, "high": 0.95},
    "employment_driven": {"low": 5000, "medium": 20000, "high": 50000},
    "tax_contribution_growth": {"low": 5.0, "medium": 12.0, "high": 20.0},
    "influence_coefficient": {"low": 0.8, "medium": 1.0, "high": 1.2},
    "upstream_coverage": {"low": 40.0, "medium": 60.0, "high": 80.0},
    "midstream_coverage": {"low": 50.0, "medium": 70.0, "high": 85.0},
    "downstream_coverage": {"low": 45.0, "medium": 65.0, "high": 80.0},
    "digitalization_level": {"low": 40.0, "medium": 60.0, "high": 80.0},
}

GOV_WEIGHTS = {
    "fiscal_leverage": 0.30,
    "industry_driving": 0.35,
    "industry_chain": 0.35,
}


class GovernmentAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.name = "GovernmentAnalyzer"
        self.benchmarks = GOV_BENCHMARKS
        self.weights = GOV_WEIGHTS
        self.data_source_info = get_data_source_info()

    def _calculate_score(
        self,
        value: float,
        metric: str,
        higher_is_better: bool = True,
    ) -> float:
        bench = self.benchmarks.get(metric)
        if not bench:
            return 60.0

        if higher_is_better:
            if value >= bench["high"]:
                return 95.0
            elif value >= bench["medium"]:
                return 75.0 + (value - bench["medium"]) / (bench["high"] - bench["medium"]) * 20
            elif value >= bench["low"]:
                return 50.0 + (value - bench["low"]) / (bench["medium"] - bench["low"]) * 25
            else:
                return 30.0 + (value / bench["low"]) * 20
        else:
            if value <= bench["low"]:
                return 95.0
            elif value <= bench["medium"]:
                return 75.0 - (value - bench["low"]) / (bench["medium"] - bench["low"]) * 20
            elif value <= bench["high"]:
                return 50.0 - (value - bench["medium"]) / (bench["high"] - bench["medium"]) * 25
            else:
                return max(10.0, 30.0 - ((value - bench["high"]) / bench["high"]) * 30)

    def analyze_fiscal_leverage(self, data: dict[str, Any]) -> dict[str, Any]:
        results = {
            "fiscal_leverage_score": 0.0,
            "deficit_rate": 0.0,
            "fiscal_self_sufficiency": 0.0,
            "funding_efficiency": 0.0,
            "sustainability": {},
            "components": {},
            "benchmarks": {},
        }

        if "expenditure" in data and "revenue" in data and "gdp" in data:
            deficit = data["expenditure"] - data["revenue"]
            deficit_rate = (deficit / data["gdp"] * 100) if data["gdp"] != 0 else 0
            results["deficit_rate"] = round(deficit_rate, 2)
            score = self._calculate_score(deficit_rate, "deficit_rate", higher_is_better=False)
            results["components"]["deficit_rate"] = {
                "value": round(deficit_rate, 2),
                "unit": "%",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["deficit_rate"] = self.benchmarks.get("deficit_rate", {})

        if "revenue" in data and "expenditure" in data:
            self_sufficiency = (data["revenue"] / data["expenditure"] * 100) if data["expenditure"] != 0 else 0
            results["fiscal_self_sufficiency"] = round(self_sufficiency, 2)
            score = self._calculate_score(self_sufficiency, "fiscal_self_sufficiency", higher_is_better=True)
            results["components"]["fiscal_self_sufficiency"] = {
                "value": round(self_sufficiency, 2),
                "unit": "%",
                "weight": 0.35,
                "score": round(score, 2),
            }
            results["benchmarks"]["fiscal_self_sufficiency"] = self.benchmarks.get("fiscal_self_sufficiency", {})

        if "fund_utilization" in data:
            funding_eff = data["fund_utilization"]
            results["funding_efficiency"] = funding_eff
            score = self._calculate_score(funding_eff, "funding_efficiency", higher_is_better=True)
            results["components"]["funding_efficiency"] = {
                "value": funding_eff,
                "unit": "",
                "weight": 0.35,
                "score": round(score, 2),
            }
            results["benchmarks"]["funding_efficiency"] = self.benchmarks.get("funding_efficiency", {})

        weighted_sum = 0.0
        weight_total = 0.0
        for comp in results["components"].values():
            w = comp["weight"]
            s = comp.get("score", 60.0)
            weighted_sum += s * w
            weight_total += w

        results["fiscal_leverage_score"] = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0

        return results

    def analyze_industry_driving(self, data: dict[str, Any]) -> dict[str, Any]:
        results = {
            "driving_score": 0.0,
            "direct_effects": {},
            "indirect_effects": {},
            "input_output_analysis": {},
            "components": {},
            "benchmarks": {},
        }

        if "employment_driven" in data:
            results["direct_effects"]["employment_driven"] = data["employment_driven"]
            score = self._calculate_score(data["employment_driven"], "employment_driven", higher_is_better=True)
            results["components"]["employment"] = {
                "value": data["employment_driven"],
                "unit": "人",
                "weight": 0.35,
                "score": round(score, 2),
            }
            results["benchmarks"]["employment_driven"] = self.benchmarks.get("employment_driven", {})

        if "tax_contribution" in data:
            results["direct_effects"]["tax_contribution"] = data["tax_contribution"]
            score = self._calculate_score(data["tax_contribution"], "tax_contribution_growth", higher_is_better=True)
            results["components"]["tax_contribution"] = {
                "value": data["tax_contribution"],
                "unit": "亿元",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["tax_contribution_growth"] = self.benchmarks.get("tax_contribution_growth", {})

        if "influence_coefficient" in data:
            results["input_output_analysis"]["influence_coefficient"] = data["influence_coefficient"]
            score = self._calculate_score(data["influence_coefficient"], "influence_coefficient", higher_is_better=True)
            results["components"]["influence"] = {
                "value": data["influence_coefficient"],
                "unit": "",
                "weight": 0.35,
                "score": round(score, 2),
            }
            results["benchmarks"]["influence_coefficient"] = self.benchmarks.get("influence_coefficient", {})

        if "sensitivity_coefficient" in data:
            results["input_output_analysis"]["sensitivity_coefficient"] = data["sensitivity_coefficient"]

        if "related_industry_output" in data:
            results["indirect_effects"]["related_industry_output"] = data["related_industry_output"]

        weighted_sum = 0.0
        weight_total = 0.0
        for comp in results["components"].values():
            w = comp["weight"]
            s = comp.get("score", 60.0)
            weighted_sum += s * w
            weight_total += w

        results["driving_score"] = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0

        return results

    def analyze_industry_chain(self, data: dict[str, Any]) -> dict[str, Any]:
        results = {
            "chain_completeness_score": 0.0,
            "upstream_coverage": 0.0,
            "midstream_coverage": 0.0,
            "downstream_coverage": 0.0,
            "bottlenecks": [],
            "strengths": [],
            "modernization_level": {},
            "components": {},
            "benchmarks": {},
        }

        if "upstream_coverage" in data:
            results["upstream_coverage"] = data["upstream_coverage"]
            score = self._calculate_score(data["upstream_coverage"], "upstream_coverage", higher_is_better=True)
            results["components"]["upstream"] = {
                "value": data["upstream_coverage"],
                "unit": "%",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["upstream_coverage"] = self.benchmarks.get("upstream_coverage", {})

        if "midstream_coverage" in data:
            results["midstream_coverage"] = data["midstream_coverage"]
            score = self._calculate_score(data["midstream_coverage"], "midstream_coverage", higher_is_better=True)
            results["components"]["midstream"] = {
                "value": data["midstream_coverage"],
                "unit": "%",
                "weight": 0.40,
                "score": round(score, 2),
            }
            results["benchmarks"]["midstream_coverage"] = self.benchmarks.get("midstream_coverage", {})

        if "downstream_coverage" in data:
            results["downstream_coverage"] = data["downstream_coverage"]
            score = self._calculate_score(data["downstream_coverage"], "downstream_coverage", higher_is_better=True)
            results["components"]["downstream"] = {
                "value": data["downstream_coverage"],
                "unit": "%",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["downstream_coverage"] = self.benchmarks.get("downstream_coverage", {})

        if "bottlenecks" in data:
            results["bottlenecks"] = data["bottlenecks"]

        if "digitalization_level" in data:
            results["modernization_level"]["digitalization"] = data["digitalization_level"]
            score = self._calculate_score(data["digitalization_level"], "digitalization_level", higher_is_better=True)
            results["components"]["digitalization"] = {
                "value": data["digitalization_level"],
                "unit": "%",
                "weight": 0.0,
                "score": round(score, 2),
            }

        weighted_sum = 0.0
        weight_total = 0.0
        for comp in results["components"].values():
            w = comp["weight"]
            if w == 0:
                continue
            s = comp.get("score", 60.0)
            weighted_sum += s * w
            weight_total += w

        results["chain_completeness_score"] = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0

        return results

    def analyze_city(self, city_name: str) -> dict[str, Any]:
        city_data = get_city_data(city_name)
        if not city_data:
            raise ValueError(f"No data available for city: {city_name}")

        gov_data = self._enrich_government_data(city_data)
        return self.generate_comprehensive_report(gov_data)

    def _enrich_government_data(self, city_data: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(city_data)

        if "gdp" not in enriched and "gdp" in enriched.get("indicators", {}):
            enriched["gdp"] = enriched["indicators"]["gdp"]

        gdp = enriched.get("gdp", 30000)
        if "revenue" not in enriched:
            enriched["revenue"] = gdp * 0.15
        if "expenditure" not in enriched:
            enriched["expenditure"] = gdp * 0.18
        if "fund_utilization" not in enriched:
            enriched["fund_utilization"] = 0.82
        if "employment_driven" not in enriched:
            enriched["employment_driven"] = int(gdp * 0.5)
        if "tax_contribution" not in enriched:
            enriched["tax_contribution"] = gdp * 0.08
        if "influence_coefficient" not in enriched:
            enriched["influence_coefficient"] = 1.05
        if "sensitivity_coefficient" not in enriched:
            enriched["sensitivity_coefficient"] = 0.95
        if "upstream_coverage" not in enriched:
            enriched["upstream_coverage"] = 55.0
        if "midstream_coverage" not in enriched:
            enriched["midstream_coverage"] = 65.0
        if "downstream_coverage" not in enriched:
            enriched["downstream_coverage"] = 60.0
        if "digitalization_level" not in enriched:
            enriched["digitalization_level"] = 55.0

        return enriched

    def compare_cities(self, city_names: list[str] | None = None) -> list[dict[str, Any]]:
        if city_names is None:
            city_names = get_all_cities()

        results = []
        for city_name in city_names:
            try:
                report = self.analyze_city(city_name)
                results.append(
                    {
                        "city": city_name,
                        "fiscal_leverage_score": report["fiscal_leverage"]["fiscal_leverage_score"],
                        "industry_driving_score": report["industry_driving"]["driving_score"],
                        "industry_chain_score": report["industry_chain"]["chain_completeness_score"],
                        "overall_score": report["overall_score"],
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to analyze {city_name}: {e}")

        return sorted(results, key=lambda x: x["overall_score"], reverse=True)

    def generate_comprehensive_report(self, data: dict[str, Any]) -> dict[str, Any]:
        report = {
            "region": data.get("region", data.get("name", "未知地区")),
            "industry": data.get("industry", "未知产业"),
            "year": data.get("year", 2025),
            "overall_score": 0.0,
            "fiscal_leverage": self.analyze_fiscal_leverage(data),
            "industry_driving": self.analyze_industry_driving(data),
            "industry_chain": self.analyze_industry_chain(data),
            "policy_recommendations": [],
            "data_source": self.data_source_info.get(data.get("name", ""), {}),
        }

        fiscal_score = report["fiscal_leverage"]["fiscal_leverage_score"]
        driving_score = report["industry_driving"]["driving_score"]
        chain_score = report["industry_chain"]["chain_completeness_score"]

        report["overall_score"] = round(
            fiscal_score * self.weights["fiscal_leverage"]
            + driving_score * self.weights["industry_driving"]
            + chain_score * self.weights["industry_chain"],
            2,
        )

        if fiscal_score < 60:
            report["policy_recommendations"].append("[!] 财政杠杆风险较高：建议优化财政资金配置，提高资金使用效率")
        elif fiscal_score < 75:
            report["policy_recommendations"].append("[i] 财政杠杆中等：建议加强专项资金管理，提升投入产出比")
        else:
            report["policy_recommendations"].append("[+] 财政杠杆健康，资金使用效率良好")

        if driving_score < 60:
            report["policy_recommendations"].append("[!] 产业带动效应不足：建议加大产业扶持力度，培育产业集群")
        elif driving_score < 75:
            report["policy_recommendations"].append("[i] 产业带动效应中等：建议完善产业链配套，增强辐射效应")
        else:
            report["policy_recommendations"].append("[+] 产业带动效应显著，对区域经济贡献大")

        if chain_score < 60:
            report["policy_recommendations"].append("[!] 产业链完整性不足：针对瓶颈环节，制定专项招商政策")
        elif chain_score < 75:
            report["policy_recommendations"].append("[i] 产业链基本完整：建议补强薄弱环节，提升产业链现代化水平")
        else:
            report["policy_recommendations"].append("[+] 产业链完整度高，产业生态成熟")

        return report

    def run_full_analysis(
        self, data, save_results: bool = True, output_dir: str = "data/government_analysis", **kwargs
    ) -> dict[str, Any]:
        if isinstance(data, str):
            return self.analyze_city(data)
        elif isinstance(data, dict):
            return self.generate_comprehensive_report(data)
        else:
            raise ValueError("data must be city name (str) or city data (dict)")

    def predict(self, data) -> dict[str, Any]:
        if isinstance(data, str):
            return self.analyze_city(data)
        elif isinstance(data, dict):
            return self.generate_comprehensive_report(data)
        else:
            raise ValueError("data must be city name (str) or city data (dict)")
