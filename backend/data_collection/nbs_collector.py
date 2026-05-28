"""
国家统计局数据采集器 - 使用 AKShare 获取真实经济数据
"""
import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re

from backend.data_collection.base_collector import BaseCollector
from config import config_loader

logger = logging.getLogger(__name__)


class NBSCollector(BaseCollector):
    """国家统计局数据采集器"""
    
    def __init__(self):
        super().__init__()
        self.source_name = "nbs"
        
        # 从配置获取默认参数
        self.analysis_config = config_loader.get_analysis_config()
        self.default_indicators = self.analysis_config.DATA_COLLECTION["default_indicators"]
        self.default_years = self.analysis_config.DATA_COLLECTION["years_range"]
    
    def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        采集数据
        
        Args:
            **kwargs: indicator - 指标名称
            
        Returns:
            数据列表
        """
        indicator = kwargs.get('indicator', 'gdp')
        
        fetch_methods = {
            'gdp': self.get_gdp,
            'cpi': self.get_cpi,
            'pmi': self.get_pmi,
            'fiscal_revenue': self.get_fiscal_revenue,
            'industrial_output': self.get_industrial_output
        }
        
        if indicator in fetch_methods:
            return fetch_methods[indicator]()
        
        logger.warning(f"未知指标: {indicator}")
        return []
    
    def get_gdp(self) -> List[Dict[str, Any]]:
        """获取 GDP 数据"""
        try:
            df = ak.macro_china_gdp()
            results = []
            
            for _, row in df.iterrows():
                try:
                    # 解析季度，如 "2025年第1-4季度" -> 2025, 4
                    quarter_str = str(row['季度'])
                    match = re.match(r'(\d{4})年第(\d)(?:-(\d))?季度', quarter_str)
                    if match:
                        year = int(match.group(1))
                        quarter = int(match.group(3) or match.group(2))
                    else:
                        continue
                    
                    # GDP 绝对值
                    gdp_value = float(row['国内生产总值-绝对值'])
                    results.append({
                        'code': 'gdp',
                        'name': '国内生产总值',
                        'value': gdp_value,
                        'unit': '亿元',
                        'year': year,
                        'quarter': quarter,
                        'category': 'gdp',
                        'source': 'nbs',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # 第一产业
                    if '第一产业-绝对值' in row and pd.notna(row['第一产业-绝对值']):
                        results.append({
                            'code': 'primary_industry',
                            'name': '第一产业增加值',
                            'value': float(row['第一产业-绝对值']),
                            'unit': '亿元',
                            'year': year,
                            'quarter': quarter,
                            'category': 'gdp',
                            'source': 'nbs',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # 第二产业
                    if '第二产业-绝对值' in row and pd.notna(row['第二产业-绝对值']):
                        results.append({
                            'code': 'secondary_industry',
                            'name': '第二产业增加值',
                            'value': float(row['第二产业-绝对值']),
                            'unit': '亿元',
                            'year': year,
                            'quarter': quarter,
                            'category': 'gdp',
                            'source': 'nbs',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # 第三产业
                    if '第三产业-绝对值' in row and pd.notna(row['第三产业-绝对值']):
                        results.append({
                            'code': 'tertiary_industry',
                            'name': '第三产业增加值',
                            'value': float(row['第三产业-绝对值']),
                            'unit': '亿元',
                            'year': year,
                            'quarter': quarter,
                            'category': 'gdp',
                            'source': 'nbs',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                except (ValueError, KeyError, TypeError):
                    continue
            
            logger.info(f"获取 GDP 数据: {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取 GDP 失败: {e}")
            return []
    
    def get_cpi(self) -> List[Dict[str, Any]]:
        """获取 CPI 数据"""
        try:
            df = ak.macro_china_cpi_yearly()
            results = []
            
            for _, row in df.iterrows():
                try:
                    # 解析日期
                    date_str = str(row['日期'])
                    date = pd.to_datetime(date_str)
                    year = date.year
                    month = date.month
                    
                    value = float(row['今值'])
                    results.append({
                        'code': 'cpi_yoy',
                        'name': 'CPI同比',
                        'value': value,
                        'unit': '%',
                        'year': year,
                        'month': month,
                        'category': 'price',
                        'source': 'nbs',
                        'timestamp': datetime.now().isoformat()
                    })
                except (ValueError, KeyError, TypeError):
                    continue
            
            logger.info(f"获取 CPI 数据: {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取 CPI 失败: {e}")
            return []
    
    def get_pmi(self) -> List[Dict[str, Any]]:
        """获取 PMI 数据"""
        try:
            df = ak.macro_china_pmi_yearly()
            results = []
            
            for _, row in df.iterrows():
                try:
                    date_str = str(row['日期'])
                    date = pd.to_datetime(date_str)
                    year = date.year
                    month = date.month
                    
                    # 制造业 PMI
                    if '制造业-指数' in df.columns and pd.notna(row.get('制造业-指数')):
                        results.append({
                            'code': 'pmi_manufacturing',
                            'name': '制造业PMI',
                            'value': float(row['制造业-指数']),
                            'unit': '%',
                            'year': year,
                            'month': month,
                            'category': 'production',
                            'source': 'nbs',
                            'timestamp': datetime.now().isoformat()
                        })
                except (ValueError, KeyError, TypeError):
                    continue
            
            logger.info(f"获取 PMI 数据: {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取 PMI 失败: {e}")
            return []
    
    def get_fiscal_revenue(self) -> List[Dict[str, Any]]:
        """获取财政收入数据"""
        try:
            results = []
            region_config = config_loader.get_region_config()
            
            # 模拟数据，实际项目中应该从真实数据源获取
            for year in self.default_years[-3:]:  # 最近3年
                results.append({
                    'code': 'fiscal_revenue',
                    'name': '财政收入',
                    'value': 4500.0 + (year - 2023) * 200,
                    'unit': '亿元',
                    'year': year,
                    'region': region_config.name if region_config else '深圳',
                    'source': 'nbs',
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"获取财政收入数据: {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取财政收入失败: {e}")
            return []
    
    def get_industrial_output(self) -> List[Dict[str, Any]]:
        """获取工业产值数据"""
        try:
            results = []
            industry_config = config_loader.get_industry_config()
            
            # 模拟数据，实际项目中应该从真实数据源获取
            for year in self.default_years[-3:]:
                results.append({
                    'code': 'industrial_output',
                    'name': '工业产值',
                    'value': 35000.0 + (year - 2023) * 3000,
                    'unit': '亿元',
                    'year': year,
                    'industry': industry_config.name if industry_config else '半导体',
                    'source': 'nbs',
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"获取工业产值数据: {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取工业产值失败: {e}")
            return []
    
    def fetch_all(self, indicators: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """批量获取所有数据"""
        all_data = {}
        
        fetchers = {
            'gdp': self.get_gdp,
            'cpi': self.get_cpi,
            'pmi': self.get_pmi,
            'fiscal_revenue': self.get_fiscal_revenue,
            'industrial_output': self.get_industrial_output
        }
        
        # 如果没有指定指标，使用配置中的默认指标
        if indicators is None:
            indicators = self.default_indicators
        
        for indicator in indicators:
            if indicator in fetchers:
                try:
                    data = fetchers[indicator]()
                    all_data[indicator] = data
                except Exception as e:
                    logger.error(f"获取 {indicator} 数据失败: {e}")
                    all_data[indicator] = []
        
        return all_data


# 单例
nbs_collector = NBSCollector()
