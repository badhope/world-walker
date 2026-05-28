"""
分析配置
"""
from typing import Dict, Any


class AnalysisConfig:
    """分析配置类"""
    
    # 默认分析参数
    DEFAULT_YEAR = 2025
    DEFAULT_REGION = "深圳"
    DEFAULT_INDUSTRY = "半导体"
    
    # 分析维度开关
    ENABLED_ANALYSES = {
        "business_cost": True,
        "supply_chain": True,
        "policy_benefits": True,
        "fiscal_leverage": True,
        "industry_driving": True,
        "industry_chain": True
    }
    
    # 可视化配置
    VISUALIZATION = {
        "theme": "plotly_white",
        "default_width": 1200,
        "default_height": 600,
        "color_palette": [
            "#667eea", "#764ba2", "#f093fb", "#f5576c",
            "#4facfe", "#00f2fe", "#43e97b", "#38f9d7",
            "#fa709a", "#fee140"
        ]
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置"""
        return {
            "default_year": cls.DEFAULT_YEAR,
            "default_region": cls.DEFAULT_REGION,
            "default_industry": cls.DEFAULT_INDUSTRY,
            "enabled_analyses": cls.ENABLED_ANALYSES,
            "visualization": cls.VISUALIZATION
        }
