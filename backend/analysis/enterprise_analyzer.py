"""
企业端分析器 - 面向企业的区域产业经济分析
基于真实城市数据和统计分位数基准计算评分
"""

import logging
from typing import Any

from backend.analysis.base_analyzer import BaseAnalyzer
from backend.data.city_data import (
    get_all_cities,
    get_city_data,
    get_data_source_info,
    get_score_benchmarks,
    get_score_weights,
)

logger = logging.getLogger(__name__)


class EnterpriseAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.name = "EnterpriseAnalyzer"
        self.benchmarks = get_score_benchmarks()
        self.weights = get_score_weights()
        self.data_source_info = get_data_source_info()

    def _calculate_score(
        self,
        value: float,
        metric: str,
        higher_is_better: bool = False,
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

    def analyze_business_costs(self, data: dict[str, Any]) -> dict[str, Any]:
        results = {"total_cost_score": 0.0, "components": {}, "benchmarks": {}}

        if "land_price" in data:
            score = self._calculate_score(data["land_price"], "land_price", higher_is_better=False)
            results["components"]["land_cost"] = {
                "value": data["land_price"],
                "unit": "元/平方米·年",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["land_price"] = self.benchmarks.get("land_price", {})

        if "salary_level" in data:
            score = self._calculate_score(data["salary_level"], "salary_level", higher_is_better=False)
            results["components"]["labor_cost"] = {
                "value": data["salary_level"],
                "unit": "元/月",
                "weight": 0.40,
                "score": round(score, 2),
            }
            results["benchmarks"]["salary_level"] = self.benchmarks.get("salary_level", {})

        if "energy_cost" in data:
            score = self._calculate_score(data["energy_cost"], "energy_cost", higher_is_better=False)
            results["components"]["energy_cost"] = {
                "value": data["energy_cost"],
                "unit": "元/千瓦时",
                "weight": 0.20,
                "score": round(score, 2),
            }
            results["benchmarks"]["energy_cost"] = self.benchmarks.get("energy_cost", {})

        if "financing_cost" in data:
            score = self._calculate_score(data["financing_cost"], "financing_cost", higher_is_better=False)
            results["components"]["financing_cost"] = {
                "value": data["financing_cost"],
                "unit": "%",
                "weight": 0.10,
                "score": round(score, 2),
            }
            results["benchmarks"]["financing_cost"] = self.benchmarks.get("financing_cost", {})

        weighted_sum = 0.0
        weight_total = 0.0
        for comp in results["components"].values():
            w = comp["weight"]
            s = comp.get("score", 60.0)
            weighted_sum += s * w
            weight_total += w

        results["total_cost_score"] = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0

        return results

    def analyze_supply_chain(self, data: dict[str, Any]) -> dict[str, Any]:
        results = {
            "supply_chain_score": 0.0,
            "localization_rate": 0.0,
            "response_efficiency": {},
            "agglomeration_index": 0.0,
            "components": {},
            "benchmarks": {},
        }

        if "local_support_rate" in data:
            results["localization_rate"] = data["local_support_rate"]
            score = self._calculate_score(data["local_support_rate"], "local_support_rate", higher_is_better=True)
            results["components"]["localization"] = {
                "value": data["local_support_rate"],
                "unit": "%",
                "weight": 0.45,
                "score": round(score, 2),
            }
            results["benchmarks"]["local_support_rate"] = self.benchmarks.get("local_support_rate", {})

        if "avg_delivery_time" in data:
            results["response_efficiency"]["avg_delivery_time"] = data["avg_delivery_time"]
            score = self._calculate_score(data["avg_delivery_time"], "avg_delivery_time", higher_is_better=False)
            results["components"]["delivery"] = {
                "value": data["avg_delivery_time"],
                "unit": "天",
                "weight": 0.25,
                "score": round(score, 2),
            }
            results["benchmarks"]["avg_delivery_time"] = self.benchmarks.get("avg_delivery_time", {})

        if "location_quotient" in data:
            results["agglomeration_index"] = data["location_quotient"]
            score = self._calculate_score(data["location_quotient"], "location_quotient", higher_is_better=True)
            results["components"]["agglomeration"] = {
                "value": data["location_quotient"],
                "unit": "",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["location_quotient"] = self.benchmarks.get("location_quotient", {})

        weighted_sum = 0.0
        weight_total = 0.0
        for comp in results["components"].values():
            w = comp["weight"]
            s = comp.get("score", 60.0)
            weighted_sum += s * w
            weight_total += w

        results["supply_chain_score"] = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0

        return results

    def analyze_policy_benefits(self, data: dict[str, Any]) -> dict[str, Any]:
        results = {
            "policy_benefit_score": 0.0,
            "tax_incentives": {},
            "subsidies": {},
            "government_efficiency": {},
            "components": {},
            "benchmarks": {},
        }

        if "tax_reduction" in data:
            results["tax_incentives"]["actual_reduction"] = data["tax_reduction"]
            score = self._calculate_score(data["tax_reduction"], "tax_reduction", higher_is_better=True)
            results["components"]["tax_reduction"] = {
                "value": data["tax_reduction"],
                "unit": "亿元",
                "weight": 0.30,
                "score": round(score, 2),
            }
            results["benchmarks"]["tax_reduction"] = self.benchmarks.get("tax_reduction", {})

        if "tax_coverage" in data:
            results["tax_incentives"]["coverage_rate"] = data["tax_coverage"]
            score = self._calculate_score(data["tax_coverage"], "tax_coverage", higher_is_better=True)
            results["components"]["tax_coverage"] = {
                "value": data["tax_coverage"],
                "unit": "%",
                "weight": 0.20,
                "score": round(score, 2),
            }
            results["benchmarks"]["tax_coverage"] = self.benchmarks.get("tax_coverage", {})

        if "rd_subsidy" in data:
            results["subsidies"]["rd_subsidy"] = data["rd_subsidy"]
            score = self._calculate_score(data["rd_subsidy"], "rd_subsidy", higher_is_better=True)
            results["components"]["rd_subsidy"] = {
                "value": data["rd_subsidy"],
                "unit": "亿元",
                "weight": 0.35,
                "score": round(score, 2),
            }
            results["benchmarks"]["rd_subsidy"] = self.benchmarks.get("rd_subsidy", {})

        if "avg_approval_time" in data:
            results["government_efficiency"]["avg_approval_time"] = data["avg_approval_time"]
            score = self._calculate_score(data["avg_approval_time"], "avg_approval_time", higher_is_better=False)
            results["components"]["approval_efficiency"] = {
                "value": data["avg_approval_time"],
                "unit": "工作日",
                "weight": 0.15,
                "score": round(score, 2),
            }
            results["benchmarks"]["avg_approval_time"] = self.benchmarks.get("avg_approval_time", {})

        weighted_sum = 0.0
        weight_total = 0.0
        for comp in results["components"].values():
            w = comp["weight"]
            s = comp.get("score", 60.0)
            weighted_sum += s * w
            weight_total += w

        results["policy_benefit_score"] = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0

        return results

    def analyze_city(self, city_name: str) -> dict[str, Any]:
        city_data = get_city_data(city_name)
        if not city_data:
            raise ValueError(f"No data available for city: {city_name}")

        return self.generate_comprehensive_report(city_data)

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
                        "business_cost_score": report["business_costs"]["total_cost_score"],
                        "supply_chain_score": report["supply_chain"]["supply_chain_score"],
                        "policy_benefit_score": report["policy_benefits"]["policy_benefit_score"],
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
            "business_costs": self.analyze_business_costs(data),
            "supply_chain": self.analyze_supply_chain(data),
            "policy_benefits": self.analyze_policy_benefits(data),
            "recommendations": [],
            "data_source": self.data_source_info.get(data.get("name", ""), {}),
        }

        cost_score = report["business_costs"]["total_cost_score"]
        supply_score = report["supply_chain"]["supply_chain_score"]
        policy_score = report["policy_benefits"]["policy_benefit_score"]

        w = self.weights
        report["overall_score"] = round(
            cost_score * w.get("business_cost", 0.35)
            + supply_score * w.get("supply_chain", 0.40)
            + policy_score * w.get("policy_benefit", 0.25),
            2,
        )

        if cost_score < 60:
            report["recommendations"].append("[!] 营商成本偏高：建议考虑成本对冲策略，如与当地政府协商土地优惠政策")
        elif cost_score < 75:
            report["recommendations"].append("[i] 营商成本中等：可探索供应链本地化降低综合成本")
        else:
            report["recommendations"].append("[+] 营商成本具有竞争力")

        if supply_score < 60:
            report["recommendations"].append("[!] 供应链配套不足：建议先建立区域供应商网络，评估分阶段投资策略")
        elif supply_score < 75:
            report["recommendations"].append("[i] 供应链配套中等：可利用区位优势逐步完善产业生态")
        else:
            report["recommendations"].append("[+] 供应链配套完善，产业集聚效应明显")

        if policy_score < 60:
            report["recommendations"].append("[!] 政策支持力度一般：建议详细研究具体产业政策，主动申请专项补贴")
        elif policy_score < 75:
            report["recommendations"].append("[i] 政策支持中等：可重点关注研发补贴和税收优惠政策")
        else:
            report["recommendations"].append("[+] 政策红利显著，政府服务效率高")

        return report

    def run_full_analysis(
        self, data, save_results: bool = True, output_dir: str = "data/enterprise_analysis", **kwargs
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
