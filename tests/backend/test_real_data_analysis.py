"""
真实数据分析模块 - 单元测试
"""

import pandas as pd
import pytest

from backend.analysis.real_data_analysis import RealDataAnalyzer


@pytest.fixture
def sample_dataframe():
    """创建一个示例数据框用于测试"""
    data = {
        "year": [2018, 2019, 2020, 2021, 2022],
        "gdp": [100, 105, 102, 110, 120],
        "gdp_primary": [10, 11, 10, 12, 13],
        "gdp_secondary": [40, 42, 40, 44, 47],
        "gdp_tertiary": [50, 52, 52, 54, 60],
        "cpi_yoy": [2.1, 2.3, 2.5, 2.8, 2.0],
        "pmi_manufacturing": [51.0, 52.0, 49.0, 50.5, 51.5],
    }
    return pd.DataFrame(data)


@pytest.fixture
def analyzer():
    """创建分析器实例"""
    return RealDataAnalyzer()


class TestRealDataAnalyzer:
    """真实数据分析器测试"""

    def test_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer is not None
        assert hasattr(analyzer, "data_cache")

    def test_calculate_correlations(self, analyzer, sample_dataframe):
        """测试相关性计算"""
        corr_matrix = analyzer._calculate_correlations(sample_dataframe)

        # 检查返回的是否是字典
        assert isinstance(corr_matrix, dict)
        # 检查是否包含预期的指标
        assert "gdp" in corr_matrix
        assert "cpi_yoy" in corr_matrix

    def test_analyze_trends(self, analyzer, sample_dataframe):
        """测试趋势分析"""
        trends = analyzer._analyze_trends(sample_dataframe)

        assert isinstance(trends, dict)
        assert "gdp" in trends
        assert "trend_direction" in trends["gdp"]
        assert "latest_value" in trends["gdp"]

        # GDP在我们的示例数据中是上升的
        assert trends["gdp"]["trend_direction"] == "up"

    def test_perform_eda(self, analyzer, sample_dataframe):
        """测试完整EDA"""
        eda_results = analyzer.perform_eda(sample_dataframe)

        assert isinstance(eda_results, dict)
        assert "summary_stats" in eda_results
        assert "missing_values" in eda_results
        assert "correlation_matrix" in eda_results
        assert "trend_analysis" in eda_results
        assert "data_period" in eda_results

        # 检查数据周期信息
        assert eda_results["data_period"]["start_year"] == 2018
        assert eda_results["data_period"]["end_year"] == 2022

    def test_generate_insights(self, analyzer, sample_dataframe):
        """测试洞察生成"""
        eda_results = analyzer.perform_eda(sample_dataframe)
        insights = analyzer.generate_insights(eda_results)

        assert isinstance(insights, list)

        # 检查每个洞察的格式
        for insight in insights:
            assert "type" in insight
            assert "title" in insight
            assert "content" in insight

    def test_get_visualization_data(self, analyzer, sample_dataframe):
        """测试可视化数据获取"""
        viz_data = analyzer.get_visualization_data(sample_dataframe)

        assert isinstance(viz_data, dict)
        assert "gdp_trend" in viz_data
        assert "cpi_trend" in viz_data
        assert "pmi_trend" in viz_data
        assert "industry_structure" in viz_data

        # 检查GDP趋势数据结构
        gdp_viz = viz_data["gdp_trend"]
        assert "years" in gdp_viz
        assert "total_gdp" in gdp_viz
        assert len(gdp_viz["years"]) == len(gdp_viz["total_gdp"])

    def test_prepare_industry_structure_data(self, analyzer, sample_dataframe):
        """测试产业结构数据准备"""
        industry_data = analyzer._prepare_industry_structure_data(sample_dataframe)

        assert isinstance(industry_data, dict)
        assert "year" in industry_data
        assert "primary" in industry_data
        assert "secondary" in industry_data
        assert "tertiary" in industry_data

        # 三个产业占比之和应该接近100%
        total = industry_data["primary"] + industry_data["secondary"] + industry_data["tertiary"]
        assert abs(total - 100.0) < 0.1  # 允许微小误差
