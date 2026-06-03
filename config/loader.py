"""
配置加载器
提供统一的配置访问接口
"""

import importlib
import logging
from pathlib import Path
from typing import Any

from config.analysis_config import AnalysisConfig
from config.industries.template import IndustryConfig
from config.regions.template import RegionConfig
from config.settings import settings

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._region_configs: dict[str, type[RegionConfig]] = {}
        self._industry_configs: dict[str, type[IndustryConfig]] = {}

        self._current_region: type[RegionConfig] | None = None
        self._current_industry: type[IndustryConfig] | None = None

        self._load_configs()
        self._initialized = True

    def _load_configs(self):
        """加载所有可用配置"""
        # 加载地区配置
        self._load_region_configs()

        # 加载产业配置
        self._load_industry_configs()

        # 设置默认配置
        self._set_default_configs()

    def _load_region_configs(self):
        """加载地区配置"""
        regions_dir = Path(__file__).parent / "regions"

        for file_path in regions_dir.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name == "template.py":
                continue

            module_name = file_path.stem
            try:
                module = importlib.import_module(f"config.regions.{module_name}")

                # 查找继承自RegionConfig的类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, RegionConfig) and attr != RegionConfig:
                        config_name = attr.name
                        if config_name:
                            self._region_configs[config_name] = attr
                            logger.debug(f"Loaded region config: {config_name}")

            except Exception as e:
                logger.error(f"Failed to load region config {module_name}: {e}")

    def _load_industry_configs(self):
        """加载产业配置"""
        industries_dir = Path(__file__).parent / "industries"

        for file_path in industries_dir.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name == "template.py":
                continue

            module_name = file_path.stem
            try:
                module = importlib.import_module(f"config.industries.{module_name}")

                # 查找继承自IndustryConfig的类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, IndustryConfig) and attr != IndustryConfig:
                        config_name = attr.name
                        if config_name:
                            self._industry_configs[config_name] = attr
                            logger.debug(f"Loaded industry config: {config_name}")

            except Exception as e:
                logger.error(f"Failed to load industry config {module_name}: {e}")

    def _set_default_configs(self):
        """设置默认配置"""
        default_region = AnalysisConfig.DEFAULT_REGION
        default_industry = AnalysisConfig.DEFAULT_INDUSTRY

        if default_region in self._region_configs:
            self._current_region = self._region_configs[default_region]
            logger.info(f"Set default region: {default_region}")
        else:
            logger.warning(f"Default region {default_region} not found")

        if default_industry in self._industry_configs:
            self._current_industry = self._industry_configs[default_industry]
            logger.info(f"Set default industry: {default_industry}")
        else:
            logger.warning(f"Default industry {default_industry} not found")

    def get_available_regions(self) -> list:
        """获取所有可用地区"""
        return list(self._region_configs.keys())

    def get_available_industries(self) -> list:
        """获取所有可用产业"""
        return list(self._industry_configs.keys())

    def get_region_config(self, region_name: str | None = None) -> type[RegionConfig] | None:
        """获取地区配置"""
        if region_name is None:
            return self._current_region

        if region_name in self._region_configs:
            return self._region_configs[region_name]

        logger.warning(f"Region config not found: {region_name}")
        return None

    def get_industry_config(self, industry_name: str | None = None) -> type[IndustryConfig] | None:
        """获取产业配置"""
        if industry_name is None:
            return self._current_industry

        if industry_name in self._industry_configs:
            return self._industry_configs[industry_name]

        logger.warning(f"Industry config not found: {industry_name}")
        return None

    def set_current_region(self, region_name: str) -> bool:
        """设置当前地区"""
        if region_name in self._region_configs:
            self._current_region = self._region_configs[region_name]
            logger.info(f"Switched to region: {region_name}")
            return True

        logger.warning(f"Failed to switch region: {region_name} not found")
        return False

    def set_current_industry(self, industry_name: str) -> bool:
        """设置当前产业"""
        if industry_name in self._industry_configs:
            self._current_industry = self._industry_configs[industry_name]
            logger.info(f"Switched to industry: {industry_name}")
            return True

        logger.warning(f"Failed to switch industry: {industry_name} not found")
        return False

    def get_analysis_config(self) -> type[AnalysisConfig]:
        """获取分析配置"""
        return AnalysisConfig

    def get_settings(self):
        """获取基础配置"""
        return settings

    def get_full_config(self) -> dict[str, Any]:
        """获取完整配置信息"""
        region_config = self._current_region
        industry_config = self._current_industry

        return {
            "settings": {
                "project_name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "api_host": settings.API_HOST,
                "api_port": settings.API_PORT,
            },
            "analysis": AnalysisConfig.get_config(),
            "current_region": region_config.to_dict() if region_config else None,
            "current_industry": industry_config.to_dict() if industry_config else None,
            "available_regions": self.get_available_regions(),
            "available_industries": self.get_available_industries(),
        }


# 单例
config_loader = ConfigLoader()
