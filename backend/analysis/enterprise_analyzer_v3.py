"""
企业分析器V3 - 基于真实城市数据
"""

import logging
from dataclasses import dataclass

import pandas as pd

# 导入真实城市数据模块
from backend.data.city_data import (
    generate_data_quality_report,
    get_city_data,
    get_data_source_info,
    get_historical_data,
    get_score_benchmarks,
    get_score_weights,
)

logger = logging.getLogger(__name__)


@dataclass
class EnterpriseAnalysis:
    """企业分析结果"""

    region: str
    year: int
    business_cost_score: float
    supply_chain_score: float
    policy_benefit_score: float
    total_score: float
    cost_details: dict[str, float]
    supply_details: dict[str, float]
    policy_details: dict[str, float]
    suggestions: list[str]
    data_source: dict[str, any]


class EnterpriseAnalyzerV3:
    """
    企业分析器V3 - 基于真实城市数据的分析系统
    改进点：
    1. 使用真实城市数据而非模拟数据
    2. 评分基准基于统计分布（25%/50%/75%分位数）
    3. 权重基于真实企业调研
    4. 有完整的数据来源说明
    """

    def __init__(self):
        self.benchmarks = get_score_benchmarks()  # 基于真实数据的基准
        self.weights = get_score_weights()  # 基于调研的权重
        self.data_source_info = get_data_source_info()
        logger.info("EnterpriseAnalyzerV3 initialized with real city data")

    def analyze(self, region: str) -> EnterpriseAnalysis:
        """分析指定城市"""
        # 获取真实城市数据
        city_data = get_city_data(region)
        if not city_data:
            raise ValueError(f"No data available for region: {region}")

        # 计算各维度得分
        cost_score, cost_details = self._calculate_business_cost(city_data)
        supply_score, supply_details = self._calculate_supply_chain(city_data)
        policy_score, policy_details = self._calculate_policy_benefit(city_data)

        # 计算总分（加权平均）
        total_score = (
            cost_score * self.weights["business_cost"]
            + supply_score * self.weights["supply_chain"]
            + policy_score * self.weights["policy_benefit"]
        )

        # 生成建议
        suggestions = self._generate_suggestions(cost_score, supply_score, policy_score, city_data)

        # 获取数据来源信息
        data_source = self.data_source_info.get(region, {})

        logger.info(f"Analysis complete for {region}: total_score={total_score:.1f}")

        return EnterpriseAnalysis(
            region=region,
            year=city_data.get("year", 2025),
            business_cost_score=cost_score,
            supply_chain_score=supply_score,
            policy_benefit_score=policy_score,
            total_score=total_score,
            cost_details=cost_details,
            supply_details=supply_details,
            policy_details=policy_details,
            suggestions=suggestions,
            data_source=data_source,
        )

    def compare_multiple_cities(self, cities: list[str]) -> pd.DataFrame:
        """对比多个城市"""
        results = []
        for city in cities:
            try:
                analysis = self.analyze(city)
                results.append(
                    {
                        "城市": analysis.region,
                        "年份": analysis.year,
                        "营商成本": analysis.business_cost_score,
                        "供应链配套": analysis.supply_chain_score,
                        "政策红利": analysis.policy_benefit_score,
                        "综合得分": analysis.total_score,
                        "数据质量": self.data_source_info.get(city, {}).get("data_quality_score", 0),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to analyze {city}: {e}")

        df = pd.DataFrame(results)
        return df.sort_values("综合得分", ascending=False).reset_index(drop=True)

    def _calculate_score(
        self,
        value: float,
        metric: str,
        higher_is_better: bool = False,
    ) -> float:
        """
        基于真实基准值计算单个指标得分
        基准值：low (25%), medium (50%), high (75%)
        """
        bench = self.benchmarks.get(metric)
        if not bench:
            return 60.0  # 默认分

        if higher_is_better:
            # 值越高越好（如本地配套率）
            if value >= bench["high"]:
                return 95.0
            elif value >= bench["medium"]:
                return 75.0 + (value - bench["medium"]) / (bench["high"] - bench["medium"]) * 20
            elif value >= bench["low"]:
                return 50.0 + (value - bench["low"]) / (bench["medium"] - bench["low"]) * 25
            else:
                return 30.0 + (value / bench["low"]) * 20
        else:
            # 值越低越好（如土地价格）
            if value <= bench["low"]:
                return 95.0
            elif value <= bench["medium"]:
                return 75.0 - (value - bench["low"]) / (bench["medium"] - bench["low"]) * 20
            elif value <= bench["high"]:
                return 50.0 - (value - bench["medium"]) / (bench["high"] - bench["medium"]) * 25
            else:
                return 30.0 - ((value - bench["high"]) / bench["high"]) * 30

    def _calculate_business_cost(self, data: dict) -> tuple[float, dict[str, float]]:
        """计算营商成本维度得分（越低越好）"""
        land_score = self._calculate_score(data["land_price"], "land_price", higher_is_better=False)
        salary_score = self._calculate_score(data["salary_level"], "salary_level", higher_is_better=False)
        energy_score = self._calculate_score(data["energy_cost"], "energy_cost", higher_is_better=False)
        financing_score = self._calculate_score(data["financing_cost"], "financing_cost", higher_is_better=False)

        total = land_score * 0.35 + salary_score * 0.40 + energy_score * 0.15 + financing_score * 0.10

        details = {
            "土地价格": data["land_price"],
            "平均工资": data["salary_level"],
            "能源成本": data["energy_cost"],
            "融资成本": data["financing_cost"],
            "土地价格得分": land_score,
            "平均工资得分": salary_score,
            "能源成本得分": energy_score,
            "融资成本得分": financing_score,
        }
        return total, details

    def _calculate_supply_chain(self, data: dict) -> tuple[float, dict[str, float]]:
        """计算供应链配套维度得分（越高越好）"""
        support_score = self._calculate_score(data["local_support_rate"], "local_support_rate", higher_is_better=True)
        delivery_score = self._calculate_score(data["avg_delivery_time"], "avg_delivery_time", higher_is_better=False)
        location_score = self._calculate_score(data["location_quotient"], "location_quotient", higher_is_better=True)

        total = support_score * 0.45 + delivery_score * 0.25 + location_score * 0.30

        details = {
            "本地配套率": data["local_support_rate"],
            "平均交付周期": data["avg_delivery_time"],
            "区位熵": data["location_quotient"],
            "供应商数量": data.get("supplier_count", 0),
            "本地配套率得分": support_score,
            "交付周期得分": delivery_score,
            "产业集聚度得分": location_score,
        }
        return total, details

    def _calculate_policy_benefit(self, data: dict) -> tuple[float, dict[str, float]]:
        """计算政策红利维度得分（越高越好）"""
        tax_red_score = self._calculate_score(data["tax_reduction"], "tax_reduction", higher_is_better=True)
        tax_cov_score = self._calculate_score(data["tax_coverage"], "tax_coverage", higher_is_better=True)
        rd_score = self._calculate_score(data["rd_subsidy"], "rd_subsidy", higher_is_better=True)
        approval_score = self._calculate_score(data["avg_approval_time"], "avg_approval_time", higher_is_better=False)

        total = tax_red_score * 0.30 + tax_cov_score * 0.20 + rd_score * 0.35 + approval_score * 0.15

        details = {
            "减税降费": data["tax_reduction"],
            "政策覆盖率": data["tax_coverage"],
            "研发补贴": data["rd_subsidy"],
            "平均审批时间": data["avg_approval_time"],
            "减税降费得分": tax_red_score,
            "政策覆盖率得分": tax_cov_score,
            "研发补贴得分": rd_score,
            "审批效率得分": approval_score,
        }
        return total, details

    def _generate_suggestions(
        self,
        cost_score: float,
        supply_score: float,
        policy_score: float,
        data: dict,
    ) -> list[str]:
        """生成针对性建议"""
        suggestions = []

        if cost_score < 60:
            suggestions.append("[!] 营商成本偏高：建议考虑成本对冲策略，如与当地政府协商土地优惠政策")
        elif cost_score < 75:
            suggestions.append("[i] 营商成本中等：可探索供应链本地化降低综合成本")
        else:
            suggestions.append("[+] 营商成本具有竞争力")

        if supply_score < 60:
            suggestions.append("[!] 供应链配套不足：建议先建立区域供应商网络，评估分阶段投资策略")
        elif supply_score < 75:
            suggestions.append("[i] 供应链配套中等：可利用区位优势逐步完善产业生态")
        else:
            suggestions.append("[+] 供应链配套完善，产业集聚效应明显")

        if policy_score < 60:
            suggestions.append("[!] 政策支持力度一般：建议详细研究具体产业政策，主动申请专项补贴")
        elif policy_score < 75:
            suggestions.append("[i] 政策支持中等：可重点关注研发补贴和税收优惠政策")
        else:
            suggestions.append("[+] 政策红利显著，政府服务效率高")

        # 基于城市特点的建议
        if data.get("industry_high_tech_ratio", 0) > 40:
            suggestions.append("[i] 该城市高新技术产业占比高，适合科技型企业布局")

        return suggestions


def run_semiconductor_fab_location_analysis() -> dict[str, any]:
    """
    企业选址案例分析：半导体制造企业选址
    业务背景：某大型半导体制造企业计划在中国新建12英寸晶圆厂
    候选城市：深圳、上海、成都
    分析维度：营商成本、供应链配套、政策红利
    """
    logger.info("Running semiconductor fab location analysis...")

    analyzer = EnterpriseAnalyzerV3()
    candidate_cities = ["深圳", "上海", "成都"]

    # 1. 逐个城市分析
    city_analyses = {}
    for city in candidate_cities:
        city_analyses[city] = analyzer.analyze(city)

    # 2. 多城市对比
    comparison_df = analyzer.compare_multiple_cities(candidate_cities)

    # 3. 获取历史数据
    historical_data = {}
    for city in candidate_cities:
        historical_data[city] = get_historical_data(city)

    # 4. 生成选址建议
    recommendation = _generate_fab_location_recommendation(city_analyses, comparison_df)

    # 5. 数据质量报告
    quality_report = generate_data_quality_report()

    result = {
        "analysis_title": "半导体制造企业选址分析报告",
        "business_background": "某大型半导体制造企业计划在中国新建12英寸晶圆厂",
        "candidate_cities": candidate_cities,
        "city_analyses": {k: v.__dict__ for k, v in city_analyses.items()},
        "comparison_table": comparison_df.to_dict(orient="records"),
        "historical_data": {k: v.to_dict(orient="records") for k, v in historical_data.items()},
        "recommendation": recommendation,
        "data_quality_report": quality_report,
        "benchmark_info": {
            "benchmarks": analyzer.benchmarks,
            "weights": analyzer.weights,
            "weight_note": get_data_source_info()["weight_note"],
            "benchmark_note": get_data_source_info()["benchmark_note"],
        },
    }

    logger.info("Semiconductor fab location analysis complete")
    return result


def _generate_fab_location_recommendation(
    city_analyses: dict[str, EnterpriseAnalysis],
    comparison_df: pd.DataFrame,
) -> dict[str, any]:
    """
    基于分析结果生成选址推荐
    考虑因素：
    1. 综合得分
    2. 供应链配套（半导体行业最重要）
    3. 成本平衡
    """
    # 供应链是半导体行业的关键因素，给予额外权重
    scores = []
    for city, analysis in city_analyses.items():
        # 半导体行业特殊权重：供应链+60%，成本+25%，政策+15%
        semiconductor_score = (
            analysis.supply_chain_score * 0.60
            + analysis.business_cost_score * 0.25
            + analysis.policy_benefit_score * 0.15
        )
        scores.append(
            {
                "city": city,
                "semiconductor_score": semiconductor_score,
                "total_score": analysis.total_score,
            }
        )

    scores_sorted = sorted(scores, key=lambda x: x["semiconductor_score"], reverse=True)
    top_city = scores_sorted[0]["city"]

    # 详细推荐理由
    top_analysis = city_analyses[top_city]

    reasons = []
    if top_analysis.supply_chain_score >= 80:
        reasons.append(f"供应链配套评分{top_analysis.supply_chain_score:.1f}分，产业集聚度高，本地配套完善")

    if top_analysis.business_cost_score >= 70:
        reasons.append(f"营商成本评分{top_analysis.business_cost_score:.1f}分，具有一定成本竞争力")

    if top_analysis.policy_benefit_score >= 75:
        reasons.append(f"政策红利评分{top_analysis.policy_benefit_score:.1f}分，研发补贴和税收优惠力度大")

    return {
        "recommended_city": top_city,
        "semiconductor_rank": [s["city"] for s in scores_sorted],
        "semiconductor_scores": {s["city"]: s["semiconductor_score"] for s in scores_sorted},
        "reasons": reasons,
        "considerations": [
            "上述分析基于当前经济数据，建议实地考察产业生态",
            "建议与当地政府沟通具体产业扶持政策",
            "建议评估人才供应和生活配套设施",
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_semiconductor_fab_location_analysis()
    print(f"分析完成！推荐城市：{result['recommendation']['recommended_city']}")
