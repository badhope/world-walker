"""
数据采集基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """数据采集基类"""

    def __init__(self):
        self.source_name = ""

    @abstractmethod
    def fetch_data(self, **kwargs) -> list[dict[str, Any]]:
        """
        采集数据

        Returns:
            数据列表
        """
        pass

    @abstractmethod
    def fetch_all(self, indicators: list[str] | None = None) -> dict[str, list[dict]]:
        """
        批量采集所有数据

        Args:
            indicators: 指定采集的指标列表，None表示全部

        Returns:
            指标名到数据列表的映射
        """
        pass
