"""
灵活的维度分析框架
支持自定义分析维度和多维度组合分析
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """分析类型"""

    DESCRIPTIVE = "descriptive"  # 描述性分析
    COMPARATIVE = "comparative"  # 对比分析
    TREND = "trend"  # 趋势分析
    CORRELATION = "correlation"  # 相关性分析
    DISTRIBUTION = "distribution"  # 分布分析
    BREAKDOWN = "breakdown"  # 分解分析
    FORECAST = "forecast"  # 预测分析
    BENCHMARK = "benchmark"  # 标杆分析
    CUSTOM = "custom"  # 自定义分析


@dataclass
class DimensionDefinition:
    """维度定义"""

    code: str  # 维度代码
    name: str  # 维度名称
    data_fields: list[str]  # 所需数据字段
    analysis_type: AnalysisType  # 分析类型
    aggregator: str | None = None  # 聚合方式: sum, avg, count, min, max
    filters: dict[str, Any] | None = None  # 过滤条件
    group_by: list[str] | None = None  # 分组字段
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外配置


@dataclass
class AnalysisResult:
    """分析结果"""

    dimension_code: str
    analysis_type: AnalysisType
    raw_data: Any
    summary: dict[str, Any]
    insights: list[str]
    visualizations: list[str]  # 可视化类型列表
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_code": self.dimension_code,
            "analysis_type": self.analysis_type.value,
            "summary": self.summary,
            "insights": self.insights,
            "visualizations": self.visualizations,
            "metadata": self.metadata,
        }


class BaseAnalyzer:
    """分析器基类"""

    def __init__(self, dimension: DimensionDefinition):
        self.dimension = dimension
        self.name = dimension.name

    def analyze(self, data: pd.DataFrame | dict[str, Any]) -> AnalysisResult:
        """执行分析"""
        raise NotImplementedError

    def preprocess(self, data: pd.DataFrame | dict[str, Any]) -> pd.DataFrame:
        """数据预处理"""
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data.copy()

        # 应用过滤器
        if self.dimension.filters:
            for col, value in self.dimension.filters.items():
                if col in df.columns:
                    df = df[df[col] == value]

        return df


class DescriptiveAnalyzer(BaseAnalyzer):
    """描述性分析器"""

    def analyze(self, data: pd.DataFrame | dict[str, Any]) -> AnalysisResult:
        df = self.preprocess(data)

        summary = {}
        for field_name in self.dimension.data_fields:
            if field_name in df.columns:
                col_data = df[field_name].dropna()
                if len(col_data) > 0:
                    summary[field_name] = {
                        "count": int(len(col_data)),
                        "mean": float(col_data.mean()),
                        "median": float(col_data.median()),
                        "std": float(col_data.std()) if len(col_data) > 1 else 0,
                        "min": float(col_data.min()),
                        "max": float(col_data.max()),
                        "sum": float(col_data.sum()),
                    }

        insights = []
        for field_name, stats in summary.items():
            if stats["std"] == 0:
                insights.append(f"{field_name} 保持稳定，无显著变化")
            elif stats["max"] > stats["mean"] * 2:
                insights.append(f"{field_name} 存在较大波动，峰值是均值的 {stats['max'] / stats['mean']:.1f} 倍")

        return AnalysisResult(
            dimension_code=self.dimension.code,
            analysis_type=self.dimension.analysis_type,
            raw_data=df,
            summary=summary,
            insights=insights,
            visualizations=["histogram", "boxplot", "summary_table"],
        )


class ComparativeAnalyzer(BaseAnalyzer):
    """对比分析器"""

    def __init__(self, dimension: DimensionDefinition):
        super().__init__(dimension)
        self.compare_fields = dimension.metadata.get("compare_fields", [])

    def analyze(self, data: pd.DataFrame | dict[str, Any]) -> AnalysisResult:
        df = self.preprocess(data)

        summary = {}
        if self.dimension.group_by and self.dimension.group_by[0] in df.columns:
            group_col = self.dimension.group_by[0]
            for field in self.dimension.data_fields:
                if field in df.columns:
                    grouped = df.groupby(group_col)[field].agg(["mean", "sum", "count"])
                    summary[field] = grouped.to_dict()

        # 计算差异
        insights = []
        for field in self.dimension.data_fields:
            if field in summary and "mean" in summary[field]:
                means = list(summary[field]["mean"].values())
                if len(means) >= 2:
                    max_mean = max(means)
                    min_mean = min(means)
                    diff_pct = (max_mean - min_mean) / min_mean * 100 if min_mean != 0 else 0
                    insights.append(f"{field} 极差为 {diff_pct:.1f}%，最大/最小比值 {max_mean / min_mean:.2f}")

        return AnalysisResult(
            dimension_code=self.dimension.code,
            analysis_type=self.dimension.analysis_type,
            raw_data=df,
            summary=summary,
            insights=insights,
            visualizations=["bar_chart", "comparison_table", "radar_chart"],
        )


class TrendAnalyzer(BaseAnalyzer):
    """趋势分析器"""

    def analyze(self, data: pd.DataFrame | dict[str, Any]) -> AnalysisResult:
        df = self.preprocess(data)

        # 确保按时间排序
        time_col = self.dimension.metadata.get("time_col", "year")
        if time_col in df.columns:
            df = df.sort_values(time_col)

        summary = {}
        for field_name in self.dimension.data_fields:
            if field_name in df.columns:
                values = df[field_name].dropna().values
                if len(values) >= 2:
                    # 计算趋势
                    x = np.arange(len(values))
                    coeffs = np.polyfit(x, values, 1)
                    slope = coeffs[0]

                    # 计算增长率
                    growth_rate = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0

                    summary[field_name] = {
                        "trend_direction": "up" if slope > 0 else "down",
                        "slope": float(slope),
                        "total_change": float(values[-1] - values[0]),
                        "total_change_pct": float(growth_rate),
                        "values": values.tolist(),
                    }

        insights = []
        for field_name, stats in summary.items():
            direction = "上升" if stats["trend_direction"] == "up" else "下降"
            insights.append(f"{field_name} 呈{direction}趋势，累计变化 {stats['total_change_pct']:.1f}%")

        return AnalysisResult(
            dimension_code=self.dimension.code,
            analysis_type=self.dimension.analysis_type,
            raw_data=df,
            summary=summary,
            insights=insights,
            visualizations=["line_chart", "area_chart", "trend_indicator"],
        )


class CorrelationAnalyzer(BaseAnalyzer):
    """相关性分析器"""

    def analyze(self, data: pd.DataFrame | dict[str, Any]) -> AnalysisResult:
        df = self.preprocess(data)

        # 选择数值列
        numeric_cols = df[self.dimension.data_fields].select_dtypes(include=[np.number]).columns.tolist()

        correlation_matrix = df[numeric_cols].corr() if len(numeric_cols) > 0 else pd.DataFrame()

        # 找出强相关
        strong_correlations = []
        if not correlation_matrix.empty:
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    corr = correlation_matrix.iloc[i, j]
                    if abs(corr) > 0.7:
                        strong_correlations.append(
                            {
                                "var1": numeric_cols[i],
                                "var2": numeric_cols[j],
                                "correlation": float(corr),
                                "strength": "强正相关" if corr > 0 else "强负相关",
                            }
                        )

        summary = {
            "correlation_matrix": correlation_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "total_pairs": len(numeric_cols) * (len(numeric_cols) - 1) // 2,
        }

        insights = []
        for corr in strong_correlations:
            insights.append(f"{corr['var1']} 与 {corr['var2']} 存在{corr['strength']}（r={corr['correlation']:.2f}）")

        if not strong_correlations:
            insights.append("未发现显著相关关系")

        return AnalysisResult(
            dimension_code=self.dimension.code,
            analysis_type=self.dimension.analysis_type,
            raw_data=df,
            summary=summary,
            insights=insights,
            visualizations=["heatmap", "scatter_plot", "correlation_matrix"],
        )


class DimensionAnalyzerFactory:
    """维度分析器工厂"""

    _analyzers = {
        AnalysisType.DESCRIPTIVE: DescriptiveAnalyzer,
        AnalysisType.COMPARATIVE: ComparativeAnalyzer,
        AnalysisType.TREND: TrendAnalyzer,
        AnalysisType.CORRELATION: CorrelationAnalyzer,
    }

    @classmethod
    def register(cls, analysis_type: AnalysisType, analyzer_class: type):
        """注册自定义分析器"""
        cls._analyzers[analysis_type] = analyzer_class

    @classmethod
    def create(cls, dimension: DimensionDefinition) -> BaseAnalyzer:
        """创建分析器"""
        analyzer_class = cls._analyzers.get(dimension.analysis_type, DescriptiveAnalyzer)
        return analyzer_class(dimension)


class FlexibleAnalysisEngine:
    """灵活的维度分析引擎"""

    def __init__(self):
        self._dimensions: dict[str, DimensionDefinition] = {}
        self._results_cache: dict[str, AnalysisResult] = {}

        self._initialize_default_dimensions()

    def _initialize_default_dimensions(self):
        """初始化默认维度"""
        default_dimensions = [
            DimensionDefinition(
                code="macro_overview",
                name="宏观经济概览",
                data_fields=["gdp", "gdp_growth", "cpi", "pmi"],
                analysis_type=AnalysisType.DESCRIPTIVE,
            ),
            DimensionDefinition(
                code="industry_comparison",
                name="产业对比分析",
                data_fields=["output_value", "growth_rate", "market_share"],
                analysis_type=AnalysisType.COMPARATIVE,
                group_by=["industry"],
            ),
            DimensionDefinition(
                code="cost_trend",
                name="成本趋势分析",
                data_fields=["land_cost", "labor_cost", "energy_cost"],
                analysis_type=AnalysisType.TREND,
                metadata={"time_col": "year"},
            ),
            DimensionDefinition(
                code="factor_correlation",
                name="要素相关性分析",
                data_fields=["gdp", "investment", "employment", "rd_intensity"],
                analysis_type=AnalysisType.CORRELATION,
            ),
            DimensionDefinition(
                code="policy_effect",
                name="政策效果评估",
                data_fields=["tax_incentive", "subsidy_amount", "satisfaction_rate"],
                analysis_type=AnalysisType.DESCRIPTIVE,
            ),
        ]

        for dim in default_dimensions:
            self.register_dimension(dim)

    def register_dimension(self, dimension: DimensionDefinition) -> bool:
        """注册分析维度"""
        self._dimensions[dimension.code] = dimension
        logger.debug(f"注册分析维度: {dimension.code} - {dimension.name}")
        return True

    def unregister_dimension(self, code: str) -> bool:
        """注销分析维度"""
        if code in self._dimensions:
            del self._dimensions[code]
            return True
        return False

    def get_dimension(self, code: str) -> DimensionDefinition | None:
        """获取维度定义"""
        return self._dimensions.get(code)

    def list_dimensions(self) -> list[DimensionDefinition]:
        """列出所有维度"""
        return list(self._dimensions.values())

    def analyze(
        self, dimension_code: str, data: pd.DataFrame | dict[str, Any], use_cache: bool = False
    ) -> AnalysisResult | None:
        """
        执行维度分析

        Args:
            dimension_code: 维度代码
            data: 数据
            use_cache: 是否使用缓存

        Returns:
            AnalysisResult
        """
        # 检查缓存
        cache_key = f"{dimension_code}:{id(data)}"
        if use_cache and cache_key in self._results_cache:
            return self._results_cache[cache_key]

        # 获取维度定义
        dimension = self._dimensions.get(dimension_code)
        if not dimension:
            logger.error(f"未知维度: {dimension_code}")
            return None

        # 创建分析器
        analyzer = DimensionAnalyzerFactory.create(dimension)

        # 执行分析
        try:
            result = analyzer.analyze(data)

            # 缓存结果
            if use_cache:
                self._results_cache[cache_key] = result

            return result
        except Exception as e:
            logger.error(f"分析失败: {dimension_code} - {e}")
            return None

    def analyze_batch(
        self, dimension_codes: list[str], data: pd.DataFrame | dict[str, Any], use_cache: bool = False
    ) -> dict[str, AnalysisResult | None]:
        """批量分析"""
        results = {}
        for code in dimension_codes:
            results[code] = self.analyze(code, data, use_cache)
        return results

    def analyze_all(self, data: pd.DataFrame | dict[str, Any]) -> dict[str, AnalysisResult]:
        """分析所有维度"""
        results = {}
        for dimension in self._dimensions.values():
            result = self.analyze(dimension.code, data)
            if result:
                results[dimension.code] = result
        return results

    def clear_cache(self):
        """清除缓存"""
        self._results_cache.clear()

    def export_dimensions(self) -> list[dict[str, Any]]:
        """导出维度配置"""
        return [
            {
                "code": dim.code,
                "name": dim.name,
                "data_fields": dim.data_fields,
                "analysis_type": dim.analysis_type.value,
                "aggregator": dim.aggregator,
                "filters": dim.filters,
                "group_by": dim.group_by,
            }
            for dim in self._dimensions.values()
        ]


# 全局实例
analysis_engine = FlexibleAnalysisEngine()


# 便捷函数
def register_analysis_dimension(
    code: str, name: str, data_fields: list[str], analysis_type: str = "descriptive", **kwargs
) -> bool:
    """便捷的维度注册函数"""
    dim = DimensionDefinition(
        code=code, name=name, data_fields=data_fields, analysis_type=AnalysisType(analysis_type), **kwargs
    )
    return analysis_engine.register_dimension(dim)


def analyze_dimension(code: str, data: dict[str, Any]) -> AnalysisResult | None:
    """执行维度分析"""
    return analysis_engine.analyze(code, data)


def analyze_all_dimensions(data: dict[str, Any]) -> dict[str, AnalysisResult]:
    """分析所有维度"""
    return analysis_engine.analyze_all(data)
