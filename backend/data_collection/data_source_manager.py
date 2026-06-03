"""
灵活的数据源管理器
支持多种数据源和动态数据源切换
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """数据源类型"""

    JSON_FILE = "json_file"
    CSV_FILE = "csv_file"
    EXCEL_FILE = "excel_file"
    API = "api"
    DATABASE = "database"
    MOCK = "mock"  # 用于测试的模拟数据


@dataclass
class DataSourceConfig:
    """数据源配置"""

    name: str
    source_type: DataSourceType
    connection_info: dict[str, Any] = field(default_factory=dict)
    tables: list[str] = field(default_factory=list)
    refresh_interval: int = 3600  # 秒
    enabled: bool = True
    priority: int = 0  # 优先级，数字越大优先级越高
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseDataSource(ABC):
    """数据源基类"""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.name = config.name
        self.source_type = config.source_type

    @abstractmethod
    def connect(self) -> bool:
        """连接数据源"""
        pass

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass

    @abstractmethod
    def fetch_data(self, query: str, **kwargs) -> pd.DataFrame | list[dict]:
        """
        获取数据

        Args:
            query: 查询条件或表名
            **kwargs: 额外参数

        Returns:
            DataFrame 或字典列表
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass

    def get_metadata(self) -> dict[str, Any]:
        """获取数据源元数据"""
        return {
            "name": self.name,
            "type": self.source_type.value,
            "tables": self.config.tables,
            "metadata": self.config.metadata,
        }


class JSONFileDataSource(BaseDataSource):
    """JSON文件数据源"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.file_path = config.connection_info.get("path", "")
        self._cache: dict[str, Any] = {}

    def connect(self) -> bool:
        try:
            if Path(self.file_path).exists():
                logger.info(f"JSON文件数据源连接成功: {self.file_path}")
                return True
            else:
                logger.warning(f"JSON文件不存在: {self.file_path}")
                return False
        except Exception as e:
            logger.error(f"JSON文件数据源连接失败: {e}")
            return False

    def disconnect(self):
        self._cache.clear()

    def fetch_data(self, query: str = "", **kwargs) -> pd.DataFrame | list[dict]:
        if not self._cache:
            self._load_json()

        if query:
            return self._cache.get(query, [])
        return self._cache

    def _load_json(self):
        """加载JSON文件"""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                self._cache = json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            self._cache = {}

    def test_connection(self) -> bool:
        return Path(self.file_path).exists()


class CSVFileDataSource(BaseDataSource):
    """CSV文件数据源"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.file_path = config.connection_info.get("path", "")

    def connect(self) -> bool:
        try:
            if Path(self.file_path).exists():
                logger.info(f"CSV文件数据源连接成功: {self.file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"CSV文件数据源连接失败: {e}")
            return False

    def disconnect(self):
        pass

    def fetch_data(self, query: str = "", **kwargs) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.file_path, **kwargs)
            if query and query in df.columns:
                return df[df[query].astype(str) == str(kwargs.get("value", ""))]
            return df
        except Exception as e:
            logger.error(f"读取CSV文件失败: {e}")
            return pd.DataFrame()

    def test_connection(self) -> bool:
        return Path(self.file_path).exists()


class MockDataSource(BaseDataSource):
    """模拟数据源（用于测试）"""

    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.mock_data = config.connection_info.get("data", {})

    def connect(self) -> bool:
        logger.info(f"模拟数据源连接: {self.name}")
        return True

    def disconnect(self):
        pass

    def fetch_data(self, query: str = "", **kwargs) -> pd.DataFrame | list[dict]:
        if query:
            return self.mock_data.get(query, [])
        return self.mock_data

    def test_connection(self) -> bool:
        return True


class DataSourceManager:
    """数据源管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._sources: dict[str, BaseDataSource] = {}
        self._configs: dict[str, DataSourceConfig] = {}
        self._data_cache: dict[str, Any] = {}
        self._last_update: dict[str, datetime] = {}

        self._initialized = True
        logger.info("DataSourceManager 初始化完成")

    def register_source(
        self, name: str, source_type: DataSourceType, connection_info: dict[str, Any], **kwargs
    ) -> bool:
        """
        注册数据源

        Args:
            name: 数据源名称
            source_type: 数据源类型
            connection_info: 连接信息
            **kwargs: 额外配置
        """
        config = DataSourceConfig(name=name, source_type=source_type, connection_info=connection_info, **kwargs)

        # 根据类型创建数据源实例
        if source_type == DataSourceType.JSON_FILE:
            source = JSONFileDataSource(config)
        elif source_type == DataSourceType.CSV_FILE:
            source = CSVFileDataSource(config)
        elif source_type == DataSourceType.MOCK:
            source = MockDataSource(config)
        else:
            logger.error(f"不支持的数据源类型: {source_type}")
            return False

        # 连接测试
        if source.connect():
            self._sources[name] = source
            self._configs[name] = config
            logger.info(f"数据源注册成功: {name}")
            return True
        else:
            logger.error(f"数据源连接失败: {name}")
            return False

    def unregister_source(self, name: str) -> bool:
        """注销数据源"""
        if name in self._sources:
            self._sources[name].disconnect()
            del self._sources[name]
            del self._configs[name]
            logger.info(f"数据源已注销: {name}")
            return True
        return False

    def get_source(self, name: str) -> BaseDataSource | None:
        """获取数据源"""
        return self._sources.get(name)

    def list_sources(self) -> list[str]:
        """列出所有数据源"""
        return list(self._sources.keys())

    def fetch_data(self, query: str, source_name: str | None = None, use_cache: bool = True, **kwargs) -> Any:
        """
        获取数据

        Args:
            query: 查询条件（通常是表名或键名）
            source_name: 数据源名称，None时自动选择
            use_cache: 是否使用缓存
            **kwargs: 额外参数

        Returns:
            数据
        """
        cache_key = f"{source_name}:{query}" if source_name else query

        # 检查缓存
        if use_cache and cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # 选择数据源
        if source_name:
            source = self._sources.get(source_name)
            if not source:
                logger.error(f"数据源不存在: {source_name}")
                return None
        else:
            # 自动选择优先级最高的数据源
            source = self._select_best_source(query)
            if not source:
                logger.error("没有可用的数据源")
                return None

        # 获取数据
        try:
            data = source.fetch_data(query, **kwargs)

            # 更新缓存
            if use_cache:
                self._data_cache[cache_key] = data
                self._last_update[cache_key] = datetime.now()

            return data
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return None

    def _select_best_source(self, query: str) -> BaseDataSource | None:
        """选择最佳数据源"""
        candidates = []

        for name, source in self._sources.items():
            if not source.config.enabled:
                continue

            # 检查数据源是否支持该查询
            if query in source.config.tables or not source.config.tables:
                candidates.append((source.config.priority, name, source))

        if candidates:
            # 返回优先级最高的
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][2]

        # 如果没有精确匹配，返回任意可用数据源
        for source in self._sources.values():
            if source.config.enabled:
                return source

        return None

    def clear_cache(self, pattern: str | None = None):
        """清除缓存"""
        if pattern:
            keys_to_remove = [k for k in self._data_cache.keys() if pattern in k]
            for k in keys_to_remove:
                del self._data_cache[k]
        else:
            self._data_cache.clear()

        logger.info(f"缓存已清除: {pattern or '全部'}")

    def get_status(self) -> dict[str, Any]:
        """获取数据源状态"""
        sources_status = []

        for name, source in self._sources.items():
            sources_status.append(
                {
                    "name": name,
                    "type": source.source_type.value,
                    "enabled": source.config.enabled,
                    "priority": source.config.priority,
                    "tables": source.config.tables,
                    "connected": source.test_connection(),
                }
            )

        return {
            "total_sources": len(self._sources),
            "enabled_sources": sum(1 for s in self._sources.values() if s.config.enabled),
            "cache_size": len(self._data_cache),
            "sources": sources_status,
        }

    def load_sources_from_config(self, config_path: str):
        """从配置文件加载数据源"""
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            for source_config in config.get("sources", []):
                self.register_source(
                    name=source_config["name"],
                    source_type=DataSourceType(source_config["type"]),
                    connection_info=source_config.get("connection", {}),
                    tables=source_config.get("tables", []),
                    priority=source_config.get("priority", 0),
                    enabled=source_config.get("enabled", True),
                )

            logger.info(f"从配置文件加载了 {len(config.get('sources', []))} 个数据源")
        except Exception as e:
            logger.error(f"加载数据源配置失败: {e}")

    def save_sources_config(self, config_path: str):
        """保存数据源配置"""
        config = {"sources": []}

        for name, source_config in self._configs.items():
            config["sources"].append(
                {
                    "name": source_config.name,
                    "type": source_config.source_type.value,
                    "connection": source_config.connection_info,
                    "tables": source_config.tables,
                    "priority": source_config.priority,
                    "enabled": source_config.enabled,
                }
            )

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"数据源配置已保存到 {config_path}")


# 全局单例
data_source_manager = DataSourceManager()


# 便捷函数
def register_data_source(name: str, source_type: str, **kwargs) -> bool:
    """注册数据源"""
    return data_source_manager.register_source(
        name=name, source_type=DataSourceType(source_type), connection_info=kwargs
    )


def fetch_from_source(query: str, source_name: str = None, **kwargs) -> Any:
    """从指定数据源获取数据"""
    return data_source_manager.fetch_data(query, source_name, **kwargs)


def list_all_sources() -> list[str]:
    """列出所有数据源"""
    return data_source_manager.list_sources()
