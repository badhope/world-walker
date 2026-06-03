"""
数据采集模块
"""

from backend.data_collection.base_collector import BaseCollector
from backend.data_collection.finance_collector import FinanceCollector
from backend.data_collection.industry_collector import IndustryCollector
from backend.data_collection.nbs_collector import NBSCollector

__all__ = ["BaseCollector", "NBSCollector", "FinanceCollector", "IndustryCollector"]
