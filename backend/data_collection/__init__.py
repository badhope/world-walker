"""
数据采集模块
"""
from backend.data_collection.nbs_collector import NBSCollector
from backend.data_collection.finance_collector import FinanceCollector
from backend.data_collection.industry_collector import IndustryCollector
from backend.data_collection.base_collector import BaseCollector

__all__ = ['BaseCollector', 'NBSCollector', 'FinanceCollector', 'IndustryCollector']
