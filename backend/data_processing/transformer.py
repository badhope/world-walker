"""
数据转换模块
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformer:
    """数据转换器"""

    def __init__(self):
        pass

    def pivot_data(self, df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
        """数据透视"""
        return df.pivot(index=index, columns=columns, values=values)

    def melt_data(self, df: pd.DataFrame, id_vars: list[str], value_vars: list[str] | None = None) -> pd.DataFrame:
        """数据融合"""
        return df.melt(id_vars=id_vars, value_vars=value_vars)

    def aggregate_data(self, df: pd.DataFrame, group_by: list[str], aggregations: dict[str, str]) -> pd.DataFrame:
        """数据聚合"""
        return df.groupby(group_by).agg(aggregations).reset_index()

    def merge_data(self, left: pd.DataFrame, right: pd.DataFrame, on: str, how: str = "inner") -> pd.DataFrame:
        """数据合并"""
        return pd.merge(left, right, on=on, how=how)

    def filter_data(self, df: pd.DataFrame, conditions: dict[str, any]) -> pd.DataFrame:
        """数据筛选"""
        df_filtered = df.copy()
        for col, value in conditions.items():
            if col in df_filtered.columns:
                if isinstance(value, list):
                    df_filtered = df_filtered[df_filtered[col].isin(value)]
                else:
                    df_filtered = df_filtered[df_filtered[col] == value]
        return df_filtered

    def sort_data(self, df: pd.DataFrame, by: list[str], ascending: bool = True) -> pd.DataFrame:
        """数据排序"""
        return df.sort_values(by=by, ascending=ascending)


# 单例
data_transformer = DataTransformer()
