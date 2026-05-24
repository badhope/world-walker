"""
对比分析模块
"""
from .compare import (
    ProvinceComparisonTool,
    TrendAnalysisTool,
    StructureComparisonTool,
    VisualizationTool,
    ComparisonAgent,
    compare_provinces,
    analyze_trend,
    compare_structure,
    PROVINCE_DATA,
)

__all__ = [
    "ProvinceComparisonTool",
    "TrendAnalysisTool",
    "StructureComparisonTool",
    "VisualizationTool",
    "ComparisonAgent",
    "compare_provinces",
    "analyze_trend",
    "compare_structure",
    "PROVINCE_DATA",
]
