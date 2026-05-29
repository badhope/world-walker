"""
分析模块测试
"""
import pytest


@pytest.mark.unit
class TestIndicatorRegistry:
    """指标注册系统测试"""

    def test_indicator_registry_init(self):
        """测试 IndicatorRegistry 初始化"""
        from backend.analysis.indicator_registry import IndicatorRegistry

        registry = IndicatorRegistry()
        assert registry is not None
        assert hasattr(registry, "register")
        assert hasattr(registry, "get")
        assert hasattr(registry, "get_all")

    def test_indicator_registry_register_indicator(self):
        """测试注册指标"""
        from backend.analysis.indicator_registry import IndicatorRegistry
        from backend.analysis.indicator_registry import IndicatorDefinition, IndicatorCategory

        registry = IndicatorRegistry()
        indicator = IndicatorDefinition(
            code="test_gdp",
            name="测试GDP",
            category=IndicatorCategory.MACRO,
            unit="亿元",
            description="测试指标描述"
        )
        registry.register(indicator)

        registered = registry.get("test_gdp")
        assert registered is not None
        assert registered.code == "test_gdp"

    def test_indicator_registry_list_indicators(self):
        """测试列出指标"""
        from backend.analysis.indicator_registry import IndicatorRegistry

        registry = IndicatorRegistry()
        indicators = registry.get_all()
        assert isinstance(indicators, list)
        assert len(indicators) > 0  # 应该有默认注册的指标


@pytest.mark.unit
class TestCustomIndicators:
    """自定义指标计算引擎测试"""

    def test_custom_indicators_module_exists(self):
        """测试自定义指标模块存在"""
        from backend.analysis import custom_indicators

        assert custom_indicators is not None


@pytest.mark.unit
class TestDimensionAnalysis:
    """维度分析框架测试"""

    def test_dimension_analysis_module_exists(self):
        """测试维度分析模块存在"""
        from backend.analysis import dimension_analysis

        assert dimension_analysis is not None


@pytest.mark.unit
class TestEnterpriseAnalyzer:
    """企业分析器测试"""

    def test_enterprise_analyzer_init(self):
        """测试 EnterpriseAnalyzer 初始化"""
        from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer

        analyzer = EnterpriseAnalyzer()
        assert analyzer is not None

    def test_enterprise_analyzer_with_sample_data(self):
        """测试使用示例数据进行分析"""
        from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner

        runner = EnterpriseAnalysisRunner()
        report = runner.generate_report()

        assert report is not None
        assert isinstance(report, dict)
        assert "title" in report
        assert "region" in report
        assert "industry" in report


@pytest.mark.unit
class TestGovernmentAnalyzer:
    """政府分析器测试"""

    def test_government_analyzer_init(self):
        """测试 GovernmentAnalyzer 初始化"""
        from backend.analysis.government_analyzer import GovernmentAnalyzer

        analyzer = GovernmentAnalyzer()
        assert analyzer is not None

    def test_government_analyzer_with_sample_data(self):
        """测试使用示例数据进行分析"""
        from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner

        runner = GovernmentAnalysisRunner()
        report = runner.generate_report()

        assert report is not None
        assert isinstance(report, dict)
        assert "title" in report
        assert "region" in report
        assert "industry" in report


@pytest.mark.unit
class TestEconomicModels:
    """经济模型测试"""

    def test_economic_models_module_exists(self):
        """测试经济模型模块存在"""
        from backend.analysis import economic_models

        assert economic_models is not None
