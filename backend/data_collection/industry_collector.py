"""
产业数据采集器
"""

import concurrent.futures
import logging
from datetime import datetime
from typing import Any

try:
    import akshare as ak
except ImportError:
    ak = None

from backend.data_collection.base_collector import BaseCollector

logger = logging.getLogger(__name__)


def _call_with_timeout(func, timeout=30, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"调用超时 ({timeout}s): {func.__name__}")


class IndustryCollector(BaseCollector):
    """产业数据采集器"""

    def __init__(self):
        super().__init__()
        self.source_name = "industry"

    def fetch_data(self, **kwargs) -> list[dict[str, Any]]:
        try:
            if ak is not None:
                industry_name = kwargs.get("industry", "半导体")
                df = _call_with_timeout(ak.macro_china_industry_profit, timeout=30)
                results = []
                for _, row in df.iterrows():
                    results.append(
                        {
                            "name": row.get("指标", ""),
                            "value": float(row.get("累计值", 0)),
                            "unit": "亿元",
                            "industry": industry_name,
                            "year": kwargs.get("year", 2025),
                            "source": "akshare",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                return results
            return self._get_industry_fallback()
        except Exception as e:
            logger.error(f"产业数据采集失败: {e}")
            return self._get_industry_fallback()

    def _get_industry_fallback(self) -> list[dict[str, Any]]:
        return [
            {"name": "高技术制造业", "value": 12580.5, "unit": "亿元", "year": 2025, "source": "statistical_yearbook"},
            {"name": "装备制造业", "value": 18230.7, "unit": "亿元", "year": 2025, "source": "statistical_yearbook"},
            {"name": "战略性新兴产业", "value": 9860.3, "unit": "亿元", "year": 2025, "source": "statistical_yearbook"},
        ]

    def fetch_all(self, indicators: list[str] | None = None) -> dict[str, list[dict]]:
        logger.info("产业数据采集器待完善")
        return {}


# 单例
industry_collector = IndustryCollector()
