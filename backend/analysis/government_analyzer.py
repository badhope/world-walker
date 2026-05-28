"""
政府端分析器 - 面向政府的区域产业经济分析
"""
import logging
from typing import Dict, Any

from backend.analysis.base_analyzer import BaseAnalyzer
from config import config_loader, AnalysisConfig

logger = logging.getLogger(__name__)


class GovernmentAnalyzer(BaseAnalyzer):
    """政府端分析器"""
    
    def __init__(self):
        super().__init__()
        self.name = "GovernmentAnalyzer"
        
        # 加载配置
        self.analysis_config = config_loader.get_analysis_config()
        self.region_config = config_loader.get_region_config()
        self.industry_config = config_loader.get_industry_config()
    
    def analyze_fiscal_leverage(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析财政杠杆率
        
        Args:
            data: 包含财政收入、支出、GDP等数据的字典
        
        Returns:
            财政杠杆分析结果
        """
        results = {
            "fiscal_leverage_score": 0.0,
            "deficit_rate": 0.0,
            "fiscal_self_sufficiency": 0.0,
            "funding_efficiency": 0.0,
            "sustainability": {}
        }
        
        # 计算赤字率
        if "expenditure" in data and "revenue" in data and "gdp" in data:
            deficit = data["expenditure"] - data["revenue"]
            results["deficit_rate"] = (deficit / data["gdp"] * 100) if data["gdp"] != 0 else 0
        
        # 计算财政自给率
        if "revenue" in data and "expenditure" in data:
            results["fiscal_self_sufficiency"] = (
                data["revenue"] / data["expenditure"] * 100
            ) if data["expenditure"] != 0 else 0
        
        # 资金使用效率
        if "special_funds" in data:
            results["funding_efficiency"] = data.get("fund_utilization", 0.8)
        
        results["fiscal_leverage_score"] = AnalysisConfig.DEFAULT_SCORES["fiscal_leverage"]
        
        return results
    
    def analyze_industry_driving(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析产业带动系数
        
        Args:
            data: 包含产业增加值、就业、投入产出表等数据的字典
        
        Returns:
            产业带动分析结果
        """
        results = {
            "driving_score": 0.0,
            "direct_effects": {},
            "indirect_effects": {},
            "input_output_analysis": {}
        }
        
        if "employment_driven" in data:
            results["direct_effects"]["employment_driven"] = data["employment_driven"]
        
        if "tax_contribution" in data:
            results["direct_effects"]["tax_contribution"] = data["tax_contribution"]
        
        if "related_industry_output" in data:
            results["indirect_effects"]["related_industry_output"] = data["related_industry_output"]
        
        if "influence_coefficient" in data:
            results["input_output_analysis"]["influence_coefficient"] = data["influence_coefficient"]
        
        if "sensitivity_coefficient" in data:
            results["input_output_analysis"]["sensitivity_coefficient"] = data["sensitivity_coefficient"]
        
        results["driving_score"] = AnalysisConfig.DEFAULT_SCORES["industry_driving"]
        
        return results
    
    def analyze_industry_chain(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析产业链补全度
        
        Args:
            data: 包含产业链环节、关键技术等数据的字典
            
        Returns:
            产业链分析结果
        """
        results = {
            "chain_completeness_score": 0.0,
            "upstream_coverage": 0.0,
            "midstream_coverage": 0.0,
            "downstream_coverage": 0.0,
            "bottlenecks": [],
            "strengths": [],
            "modernization_level": {},
            "chain_links": [],
            "key_indicators": {}
        }
        
        # 从配置加载产业链信息
        if self.industry_config:
            results["chain_links"] = self.industry_config.chain_links
            results["key_indicators"] = self.industry_config.key_indicators
            
            # 如果数据中没有提供瓶颈，使用配置中的
            if "bottlenecks" not in data and hasattr(self.industry_config, 'chain_analysis'):
                results["bottlenecks"] = self.industry_config.chain_analysis.get("key_bottlenecks", [])
        
        if "upstream_coverage" in data:
            results["upstream_coverage"] = data["upstream_coverage"]
        
        if "midstream_coverage" in data:
            results["midstream_coverage"] = data["midstream_coverage"]
        
        if "downstream_coverage" in data:
            results["downstream_coverage"] = data["downstream_coverage"]
        
        if "bottlenecks" in data:
            results["bottlenecks"] = data["bottlenecks"]
        
        if "digitalization_level" in data:
            results["modernization_level"]["digitalization"] = data["digitalization_level"]
        
        # 计算综合覆盖度
        avg_coverage = (
            results["upstream_coverage"] +
            results["midstream_coverage"] +
            results["downstream_coverage"]
        ) / 3
        results["chain_completeness_score"] = avg_coverage * 100
        
        return results
    
    def generate_comprehensive_report(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成政府端综合分析报告
        
        Args:
            data: 综合数据字典
            
        Returns:
            完整分析报告
        """
        # 从配置获取默认地区和产业
        default_region = self.region_config.name if self.region_config else "未知地区"
        default_industry = self.industry_config.name if self.industry_config else "未知产业"
        default_year = self.analysis_config.DEFAULT_YEAR
        
        report = {
            "region": data.get("region", default_region),
            "industry": data.get("industry", default_industry),
            "year": data.get("year", default_year),
            "overall_score": 0.0,
            "fiscal_leverage": self.analyze_fiscal_leverage(data),
            "industry_driving": self.analyze_industry_driving(data),
            "industry_chain": self.analyze_industry_chain(data),
            "policy_recommendations": []
        }
        
        # 计算综合得分
        scores = [
            report["fiscal_leverage"]["fiscal_leverage_score"],
            report["industry_driving"]["driving_score"],
            report["industry_chain"]["chain_completeness_score"]
        ]
        report["overall_score"] = sum(scores) / len(scores)
        
        # 从配置获取阈值
        thresholds = self.analysis_config.THRESHOLDS
        
        # 生成政策建议
        if report["fiscal_leverage"]["fiscal_leverage_score"] < thresholds.get("fiscal_healthy", 70):
            report["policy_recommendations"].append("优化财政资金配置，提高资金使用效率")
        
        if report["industry_chain"]["chain_completeness_score"] < thresholds.get("supply_chain_good", 75):
            report["policy_recommendations"].append("针对产业链瓶颈环节，制定专项招商政策")
        
        return report
