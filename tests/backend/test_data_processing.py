"""
数据处理模块测试
"""

import pandas as pd
import pytest


@pytest.mark.unit
class TestDataCleaner:
    """数据清洗器测试"""

    def test_data_cleaner_init(self):
        """测试 DataCleaner 初始化"""
        from backend.data_processing.cleaner import DataCleaner

        cleaner = DataCleaner()
        assert cleaner is not None

    def test_data_cleaner_fill_missing(self):
        """测试填充缺失值"""
        from backend.data_processing.cleaner import DataCleaner

        cleaner = DataCleaner()
        data = pd.DataFrame({"value": [1, None, 3, None, 5]})

        filled = cleaner.fill_missing(data, method="zero")
        assert filled["value"].isna().sum() == 0

    def test_data_cleaner_detect_missing(self):
        """测试检测缺失值"""
        from backend.data_processing.cleaner import DataCleaner

        cleaner = DataCleaner()
        data = pd.DataFrame({"value": [1, None, 3, None, 5]})

        missing_info = cleaner.detect_missing(data)
        assert "total_missing" in missing_info
        assert missing_info["total_missing"] == 2


@pytest.mark.unit
class TestDataTransformer:
    """数据转换器测试"""

    def test_data_transformer_init(self):
        """测试 DataTransformer 初始化"""
        from backend.data_processing.transformer import DataTransformer

        transformer = DataTransformer()
        assert transformer is not None

    def test_data_transformer_pivot_data(self):
        """测试数据透视"""
        from backend.data_processing.transformer import DataTransformer

        transformer = DataTransformer()
        data = pd.DataFrame({"year": [2020, 2020, 2021, 2021], "type": ["a", "b", "a", "b"], "value": [10, 20, 30, 40]})

        pivoted = transformer.pivot_data(data, index="year", columns="type", values="value")
        assert "a" in pivoted.columns
        assert "b" in pivoted.columns

    def test_data_transformer_filter_data(self):
        """测试数据筛选"""
        from backend.data_processing.transformer import DataTransformer

        transformer = DataTransformer()
        data = pd.DataFrame({"id": [1, 2, 3, 4, 5], "value": [10, 20, 30, 40, 50]})

        filtered = transformer.filter_data(data, {"id": [1, 3, 5]})
        assert len(filtered) == 3

    def test_data_transformer_aggregate_data(self):
        """测试数据聚合"""
        from backend.data_processing.transformer import DataTransformer

        transformer = DataTransformer()
        data = pd.DataFrame({"category": ["a", "a", "b", "b"], "value": [10, 20, 30, 40]})

        aggregated = transformer.aggregate_data(data, group_by=["category"], aggregations={"value": "sum"})
        assert len(aggregated) == 2


@pytest.mark.unit
class TestDataValidator:
    """数据验证器测试"""

    def test_data_validator_init(self):
        """测试 DataValidator 初始化"""
        from backend.data_processing.validator import DataValidator

        validator = DataValidator()
        assert validator is not None

    def test_data_validator_validate_required_columns(self):
        """测试验证必需列"""
        from backend.data_processing.validator import DataValidator

        validator = DataValidator()
        data = pd.DataFrame({"region": ["深圳"], "year": [2025], "gdp": [35000]})

        result = validator.validate_required_columns(data, ["region", "year"])
        assert result["valid"] is True
        assert len(result["missing_columns"]) == 0

    def test_data_validator_missing_required_columns(self):
        """测试缺失必需列"""
        from backend.data_processing.validator import DataValidator

        validator = DataValidator()
        data = pd.DataFrame({"region": ["深圳"]})

        result = validator.validate_required_columns(data, ["region", "year"])
        assert result["valid"] is False
        assert len(result["missing_columns"]) == 1
        assert "year" in result["missing_columns"]

    def test_data_validator_validate_value_ranges(self):
        """测试验证值范围"""
        from backend.data_processing.validator import DataValidator

        validator = DataValidator()
        data = pd.DataFrame({"value": [-10, 0, 50, 100, 150]})

        result = validator.validate_value_ranges(data, {"value": (0, 100)})
        assert result["valid"] is False
        assert "value" in result["violations"]

    def test_data_validator_validate_not_null(self):
        """测试验证非空"""
        from backend.data_processing.validator import DataValidator

        validator = DataValidator()
        data = pd.DataFrame({"value": [1, None, 3, None, 5]})

        result = validator.validate_not_null(data, ["value"])
        assert result["valid"] is False
        assert "value" in result["null_columns"]


@pytest.mark.integration
class TestDataProcessingWorkflow:
    """数据处理工作流集成测试"""

    def test_complete_data_processing_pipeline(self):
        """测试完整的数据处理流程"""
        from backend.data_processing.cleaner import DataCleaner
        from backend.data_processing.transformer import DataTransformer
        from backend.data_processing.validator import DataValidator

        # 原始数据
        raw_data = pd.DataFrame({"id": [1, 2, 3, 4, 5], "value": [10, 20, 30, 40, 50]})

        # 1. 清洗（检测缺失，填充）
        cleaner = DataCleaner()
        missing_info = cleaner.detect_missing(raw_data)

        # 2. 验证
        validator = DataValidator()
        validation_result = validator.validate_required_columns(raw_data, ["id", "value"])

        # 3. 转换
        transformer = DataTransformer()
        filtered = transformer.filter_data(raw_data, {"id": [1, 2, 3]})

        assert len(filtered) == 3
        assert validation_result.get("valid", True)  # 流程完成
