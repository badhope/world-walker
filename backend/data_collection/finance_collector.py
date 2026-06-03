"""
金融数据采集器 - 人民银行等金融数据
"""

import concurrent.futures
import logging
from datetime import datetime
from typing import Any

import pandas as pd

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


class FinanceCollector(BaseCollector):
    """金融数据采集器"""

    def __init__(self):
        super().__init__()
        self.source_name = "pbc"

    def fetch_data(self, **kwargs) -> list[dict[str, Any]]:
        """
        采集数据

        Args:
            **kwargs: indicator - 指标名称

        Returns:
            数据列表
        """
        indicator = kwargs.get("indicator", "m2")

        fetch_methods = {
            "m2": self.get_money_supply,
        }

        if indicator in fetch_methods:
            return fetch_methods[indicator]()

        logger.warning(f"未知指标: {indicator}")
        return []

    def get_money_supply(self) -> list[dict[str, Any]]:
        """获取货币供应量"""
        try:
            df = _call_with_timeout(ak.macro_china_m2_yearly, timeout=30)
            results = []

            for _, row in df.iterrows():
                try:
                    date_str = str(row["日期"])
                    date = pd.to_datetime(date_str)
                    year = date.year
                    month = date.month

                    value = float(row["今值"])
                    results.append(
                        {
                            "code": "m2_yoy",
                            "name": "M2同比",
                            "value": value,
                            "unit": "%",
                            "year": year,
                            "month": month,
                            "category": "financial",
                            "source": "pbc",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except (ValueError, KeyError, TypeError):
                    continue

            logger.info(f"获取 M2 数据: {len(results)} 条")
            return results

        except Exception as e:
            logger.error(f"获取 M2 失败: {e}")
            return []

    def fetch_all(self, indicators: list[str] | None = None) -> dict[str, list[dict]]:
        """批量获取所有数据"""
        all_data = {}

        fetchers = {
            "money_supply": self.get_money_supply,
        }

        if indicators:
            fetchers = {k: v for k, v in fetchers.items() if k in indicators}

        for name, fetcher in fetchers.items():
            try:
                data = fetcher()
                all_data[name] = data
            except Exception as e:
                logger.error(f"获取 {name} 数据失败: {e}")
                all_data[name] = []

        return all_data


# 单例
finance_collector = FinanceCollector()
