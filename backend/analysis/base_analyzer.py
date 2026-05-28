"""
基础分析器
"""
import logging
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class BaseAnalyzer:
    """基础分析器"""
    
    def __init__(self):
        self.name = "BaseAnalyzer"
    
    def summarize_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """数据摘要"""
        summary = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": float(df.memory_usage(deep=True).sum() / 1024 / 1024)  # MB
        }
        
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            summary["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        return summary
    
    def calculate_growth_rates(
        self,
        df: pd.DataFrame,
        value_col: str,
        time_col: str,
        periods: int = 1
    ) -> pd.DataFrame:
        """计算增长率"""
        df_sorted = df.sort_values(time_col).copy()
        df_sorted[f"{value_col}_growth"] = df_sorted[value_col].pct_change(periods=periods) * 100
        return df_sorted
    
    def calculate_moving_average(
        self,
        df: pd.DataFrame,
        value_col: str,
        window: int = 4
    ) -> pd.DataFrame:
        """计算移动平均"""
        df_ma = df.copy()
        df_ma[f"{value_col}_ma{window}"] = df_ma[value_col].rolling(window=window).mean()
        return df_ma
    
    def calculate_correlation(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算相关性矩阵"""
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        return df[numeric_cols].corr()
    
    def detect_trend(self, df: pd.DataFrame, value_col: str, time_col: str) -> Dict[str, Any]:
        """检测趋势"""
        df_sorted = df.sort_values(time_col).copy()
        values = df_sorted[value_col].dropna()
        
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        
        # 简单趋势检测：比较首尾值
        first = values.iloc[0]
        last = values.iloc[-1]
        
        if last > first:
            trend = "upward"
        elif last < first:
            trend = "downward"
        else:
            trend = "flat"
        
        return {
            "trend": trend,
            "change_pct": ((last - first) / first * 100) if first != 0 else None,
            "first_value": first,
            "last_value": last
        }
