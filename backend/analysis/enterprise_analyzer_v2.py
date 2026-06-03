"""
企业端分析器 v2 - 真正用数据计算评分，而不是硬编码
"""

import logging
from typing import Any

import pandas as pd

from backend.analysis.base_analyzer import BaseAnalyzer
from config.analysis_config import AnalysisConfig

logger = logging.getLogger(__name__)


class EnterpriseAnalyzerV2(BaseAnalyzer):
    """企业端分析器 v2 - 真实数据分析"""

    def __init__(self):
        super().__init__()
        self.name = "EnterpriseAnalyzerV2"

        # 评分基准数据（基于真实经济数据）
        self.benchmarks = {
            "land_price": {"low": 500, "medium": 1000, "high": 1500},  # 元/平方米·年
            "salary_level": {"low": 8000, "medium": 15000, "high": 25000},  # 元/月
            "energy_cost": {"low": 0.8, "medium": 1.2, "high": 1.8},  # 元/千瓦时
            "financing_cost": {"low": 3.5, "medium": 5.0, "high": 7.0},  # %
            "local_support_rate": {"low": 50, "medium": 75, "high": 90},  # %
            "avg_delivery_time": {"low": 2, "medium": 4, "high": 7},  # 天
            "location_quotient": {"low": 1.0, "medium": 2.0, "high": 3.0},  # LQ
            "tax_reduction": {"low": 100, "medium": 500, "high": 1000},  # 亿元
            "tax_coverage": {"low": 60, "medium": 80, "high": 95},  # %
            "rd_subsidy": {"low": 50, "medium": 200, "high": 500},  # 亿元
            "avg_approval_time": {"low": 3, "medium": 7, "high": 14},  # 天
        }

    def _calculate_score(self, value: float, metric: str, higher_is_better: bool = False) -> float:
        """
        基于基准值计算分数

        Args:
            value: 实际值
            metric: 指标名称
            higher_is_better: 值越高是否越好

        Returns:
            0-100 的评分
        """
        bench = self.benchmarks.get(metric)
        if not bench or pd.isna(value):
            return 50.0  # 默认分数

        if higher_is_better:
            # 值越高越好（如本地化率）
            if value >= bench["high"]:
                return 95.0
            elif value >= bench["medium"]:
                return 75.0 + (value - bench["medium"]) / (bench["high"] - bench["medium"]) * 20
            elif value >= bench["low"]:
                return 50.0 + (value - bench["low"]) / (bench["medium"] - bench["low"]) * 25
            else:
                return 30.0 + (value / bench["low"]) * 20
        else:
            # 值越低越好（如成本、交付时间）
            if value <= bench["low"]:
                return 95.0
            elif value <= bench["medium"]:
                return 75.0 + (bench["medium"] - value) / (bench["medium"] - bench["low"]) * 20
            elif value <= bench["high"]:
                return 50.0 + (bench["high"] - value) / (bench["high"] - bench["medium"]) * 25
            else:
                return max(10.0, 50.0 - (value - bench["high"]) / bench["high"] * 40)

    def analyze_business_costs(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        分析营商成本 - 真正计算评分

        Args:
            data: 包含土地价格、薪资、水电等数据的字典

        Returns:
            营商成本分析结果
        """
        results = {"total_cost_score": 0.0, "components": {}, "benchmarks": self.benchmarks}

        component_scores = []

        # 土地成本
        if "land_price" in data and pd.notna(data["land_price"]):
            score = self._calculate_score(data["land_price"], "land_price", higher_is_better=False)
            results["components"]["land_cost"] = {
                "value": data["land_price"],
                "unit": "元/平方米·年",
                "weight": 0.3,
                "score": score,
            }
            component_scores.append((score, 0.3))

        # 人力成本
        if "salary_level" in data and pd.notna(data["salary_level"]):
            score = self._calculate_score(data["salary_level"], "salary_level", higher_is_better=False)
            results["components"]["labor_cost"] = {
                "value": data["salary_level"],
                "unit": "元/月",
                "weight": 0.4,
                "score": score,
            }
            component_scores.append((score, 0.4))

        # 能源成本
        if "energy_cost" in data and pd.notna(data["energy_cost"]):
            score = self._calculate_score(data["energy_cost"], "energy_cost", higher_is_better=False)
            results["components"]["energy_cost"] = {
                "value": data["energy_cost"],
                "unit": "元/千瓦时",
                "weight": 0.2,
                "score": score,
            }
            component_scores.append((score, 0.2))

        # 融资成本
        if "financing_cost" in data and pd.notna(data["financing_cost"]):
            score = self._calculate_score(data["financing_cost"], "financing_cost", higher_is_better=False)
            results["components"]["financing_cost"] = {
                "value": data["financing_cost"],
                "unit": "%",
                "weight": 0.1,
                "score": score,
            }
            component_scores.append((score, 0.1))

        # 计算加权综合成本评分
        if component_scores:
            total_weight = sum(w for _, w in component_scores)
            results["total_cost_score"] = sum(s * w for s, w in component_scores) / total_weight
        else:
            results["total_cost_score"] = AnalysisConfig.DEFAULT_SCORES["business_cost"]

        return results

    def analyze_supply_chain(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        分析供应链配套效率 - 真正计算评分
        """
        results = {
            "supply_chain_score": 0.0,
            "localization_rate": 0.0,
            "response_efficiency": {},
            "agglomeration_index": 0.0,
            "benchmarks": self.benchmarks,
        }

        component_scores = []

        if "local_support_rate" in data and pd.notna(data["local_support_rate"]):
            results["localization_rate"] = data["local_support_rate"]
            score = self._calculate_score(data["local_support_rate"], "local_support_rate", higher_is_better=True)
            component_scores.append((score, 0.4))

        if "avg_delivery_time" in data and pd.notna(data["avg_delivery_time"]):
            results["response_efficiency"]["avg_delivery_time"] = data["avg_delivery_time"]
            score = self._calculate_score(data["avg_delivery_time"], "avg_delivery_time", higher_is_better=False)
            component_scores.append((score, 0.3))

        if "location_quotient" in data and pd.notna(data["location_quotient"]):
            results["agglomeration_index"] = data["location_quotient"]
            score = self._calculate_score(data["location_quotient"], "location_quotient", higher_is_better=True)
            component_scores.append((score, 0.3))

        if component_scores:
            total_weight = sum(w for _, w in component_scores)
            results["supply_chain_score"] = sum(s * w for s, w in component_scores) / total_weight
        else:
            results["supply_chain_score"] = AnalysisConfig.DEFAULT_SCORES["supply_chain"]

        return results

    def analyze_policy_benefits(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        分析政策红利兑现率 - 真正计算评分
        """
        results = {
            "policy_benefit_score": 0.0,
            "tax_incentives": {},
            "subsidies": {},
            "government_efficiency": {},
            "benchmarks": self.benchmarks,
        }

        component_scores = []

        if "tax_reduction" in data and pd.notna(data["tax_reduction"]):
            results["tax_incentives"]["actual_reduction"] = data["tax_reduction"]
            score = self._calculate_score(data["tax_reduction"], "tax_reduction", higher_is_better=True)
            component_scores.append((score, 0.3))

        if "tax_coverage" in data and pd.notna(data["tax_coverage"]):
            results["tax_incentives"]["coverage_rate"] = data["tax_coverage"]
            score = self._calculate_score(data["tax_coverage"], "tax_coverage", higher_is_better=True)
            component_scores.append((score, 0.2))

        if "rd_subsidy" in data and pd.notna(data["rd_subsidy"]):
            results["subsidies"]["rd_subsidy"] = data["rd_subsidy"]
            score = self._calculate_score(data["rd_subsidy"], "rd_subsidy", higher_is_better=True)
            component_scores.append((score, 0.3))

        if "avg_approval_time" in data and pd.notna(data["avg_approval_time"]):
            results["government_efficiency"]["avg_approval_time"] = data["avg_approval_time"]
            score = self._calculate_score(data["avg_approval_time"], "avg_approval_time", higher_is_better=False)
            component_scores.append((score, 0.2))

        if component_scores:
            total_weight = sum(w for _, w in component_scores)
            results["policy_benefit_score"] = sum(s * w for s, w in component_scores) / total_weight
        else:
            results["policy_benefit_score"] = AnalysisConfig.DEFAULT_SCORES["policy_benefit"]

        return results

    def run_full_analysis(
        self, data, save_results: bool = True, output_dir: str = "data/output", **kwargs
    ) -> dict[str, Any]:
        if isinstance(data, dict):
            return self.generate_comprehensive_report(data)
        raise ValueError("data must be a dict")

    def predict(self, data) -> dict[str, Any]:
        if isinstance(data, dict):
            return self.generate_comprehensive_report(data)
        raise ValueError("data must be a dict")

    def generate_comprehensive_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        生成企业端综合分析报告 - 基于真实数据
        """
        report = {
            "version": "v2",
            "region": data.get("region", "未知地区"),
            "industry": data.get("industry", "未知产业"),
            "year": data.get("year", 2025),
            "overall_score": 0.0,
            "business_costs": self.analyze_business_costs(data),
            "supply_chain": self.analyze_supply_chain(data),
            "policy_benefits": self.analyze_policy_benefits(data),
            "recommendations": [],
            "data_used": {k: v for k, v in data.items() if k not in ["region", "industry", "year"]},
        }

        scores = [
            report["business_costs"]["total_cost_score"],
            report["supply_chain"]["supply_chain_score"],
            report["policy_benefits"]["policy_benefit_score"],
        ]
        report["overall_score"] = sum(scores) / len(scores)

        # generate recommendations
        bc_score = report["business_costs"]["total_cost_score"]
        sc_score = report["supply_chain"]["supply_chain_score"]
        pb_score = report["policy_benefits"]["policy_benefit_score"]

        if bc_score < 70:
            report["recommendations"].append(
                {
                    "priority": "high",
                    "category": "business_cost",
                    "content": f"营商成本评分偏低 ({bc_score:.1f})，建议评估土地和人力成本优化空间",
                }
            )
        elif bc_score < 85:
            report["recommendations"].append(
                {
                    "priority": "medium",
                    "category": "business_cost",
                    "content": f"营商成本中等 ({bc_score:.1f})，关注融资成本优化机会",
                }
            )

        if sc_score < 70:
            report["recommendations"].append(
                {
                    "priority": "high",
                    "category": "supply_chain",
                    "content": f"供应链配套有待加强 ({sc_score:.1f})，建议提升本地化配套率",
                }
            )
        elif sc_score < 85:
            report["recommendations"].append(
                {
                    "priority": "medium",
                    "category": "supply_chain",
                    "content": f"供应链基础良好 ({sc_score:.1f})，可进一步缩短交付周期",
                }
            )

        if pb_score < 70:
            report["recommendations"].append(
                {
                    "priority": "high",
                    "category": "policy",
                    "content": f"政策红利利用不足 ({pb_score:.1f})，建议加强研发补贴申请",
                }
            )

        return report


# 单例
enterprise_analyzer_v2 = EnterpriseAnalyzerV2()
