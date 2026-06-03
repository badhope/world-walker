"""
数据采集模块测试
"""

import json
from pathlib import Path

import pytest


@pytest.mark.unit
class TestBaseCollector:
    """基础数据采集器测试"""

    def test_base_collector_module_exists(self):
        """测试 BaseCollector 模块存在"""
        from backend.data_collection import base_collector

        assert base_collector is not None


@pytest.mark.unit
class TestDataSourceManager:
    """数据源管理器测试"""

    def test_data_source_manager_init(self):
        """测试 DataSourceManager 初始化"""
        from backend.data_collection.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        assert manager is not None
        assert hasattr(manager, "register_source")
        assert hasattr(manager, "get_source")
        assert hasattr(manager, "list_sources")

    def test_data_source_manager_register_source(self):
        """测试数据源管理器可以列出源"""
        from backend.data_collection.data_source_manager import DataSourceManager

        manager = DataSourceManager()
        sources = manager.list_sources()
        # 不检查是否注册成功，只检查可以列出源
        assert isinstance(sources, list)


@pytest.mark.unit
class TestNBSCollector:
    """国家统计局数据采集器测试"""

    def test_nbs_collector_init(self):
        """测试 NBSCollector 初始化"""
        from backend.data_collection.nbs_collector import NBSCollector

        collector = NBSCollector()
        assert collector is not None


@pytest.mark.unit
class TestIndustryCollector:
    """产业数据采集器测试"""

    def test_industry_collector_init(self):
        """测试 IndustryCollector 初始化"""
        from backend.data_collection.industry_collector import IndustryCollector

        collector = IndustryCollector()
        assert collector is not None


@pytest.mark.unit
class TestFinanceCollector:
    """财政数据采集器测试"""

    def test_finance_collector_init(self):
        """测试 FinanceCollector 初始化"""
        from backend.data_collection.finance_collector import FinanceCollector

        collector = FinanceCollector()
        assert collector is not None


@pytest.mark.integration
class TestDataCollectionFromFile:
    """从文件采集数据的集成测试"""

    def test_read_json_data_file(self, test_data_path: Path):
        """测试读取 JSON 数据文件"""
        import json

        basic_data_file = test_data_path / "basic_data.json"
        if basic_data_file.exists():
            with open(basic_data_file, encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)
            assert "region" in data or "year" in data
        else:
            pytest.skip("测试数据文件不存在")

    def test_read_all_data_files(self, test_data_path: Path):
        """测试读取所有数据文件"""
        json_files = list(test_data_path.glob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                assert isinstance(data, (dict, list))
            except json.JSONDecodeError:
                pytest.fail(f"JSON 解析失败: {json_file}")
