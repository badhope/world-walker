"""
数据清洗模块 - 处理缺失值、异常值、数据标准化
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.cleaning_report = {}

    def _get_numeric_columns(self, df: pd.DataFrame, columns: list[str] | None) -> list[str]:
        """获取要处理的数值列"""
        if columns is None:
            return df.select_dtypes(include=[np.number]).columns.tolist()
        return [col for col in columns if col in df.columns]

    def detect_missing(self, df: pd.DataFrame) -> dict[str, any]:
        """检测缺失值"""
        missing_info = {
            "total_cells": df.size,
            "total_missing": df.isna().sum().sum(),
            "missing_ratio": df.isna().sum().sum() / df.size,
            "columns": {},
        }

        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_info["columns"][col] = {
                    "missing_count": int(missing_count),
                    "missing_ratio": missing_count / len(df),
                    "dtype": str(df[col].dtype),
                }

        return missing_info

    def fill_missing(self, df: pd.DataFrame, method: str = "linear", columns: list[str] | None = None) -> pd.DataFrame:
        """
        填充缺失值

        Args:
            df: 数据框
            method: 填充方法 (linear, mean, median, mode, forward, backward, zero)
            columns: 指定列，为空则处理所有数值列
        """
        df_clean = df.copy()
        target_columns = self._get_numeric_columns(df_clean, columns)
        categorical_cols = df_clean.select_dtypes(include=["object", "category"]).columns

        for col in target_columns:
            missing_mask = df_clean[col].isna()
            if not missing_mask.any():
                continue

            if method == "linear":
                df_clean[col] = df_clean[col].interpolate(method="linear")
            elif method == "mean":
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
            elif method == "median":
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            elif method == "mode":
                mode_val = df_clean[col].mode()
                if len(mode_val) > 0:
                    df_clean[col] = df_clean[col].fillna(mode_val[0])
            elif method == "forward":
                df_clean[col] = df_clean[col].fillna(method="ffill")
            elif method == "backward":
                df_clean[col] = df_clean[col].fillna(method="bfill")
            elif method == "zero":
                df_clean[col] = df_clean[col].fillna(0)

        for col in categorical_cols:
            if df_clean[col].isnull().sum() > 0:
                df_clean[col] = df_clean[col].fillna(
                    df_clean[col].mode()[0] if not df_clean[col].mode().empty else "unknown"
                )

        return df_clean

    def detect_outliers_zscore(
        self, df: pd.DataFrame, threshold: float = 3.0, columns: list[str] | None = None
    ) -> dict[str, any]:
        """使用 Z-score 检测异常值"""
        target_columns = self._get_numeric_columns(df, columns)
        outliers_info = {"method": "zscore", "threshold": threshold, "columns": {}}

        for col in target_columns:
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            outlier_mask = z_scores > threshold
            outlier_indices = df[col].dropna().index[outlier_mask].tolist()

            if outlier_indices:
                outliers_info["columns"][col] = {
                    "outlier_count": len(outlier_indices),
                    "outlier_ratio": len(outlier_indices) / len(df),
                    "outlier_indices": outlier_indices[:100],
                    "outlier_values": df.loc[outlier_indices, col].tolist()[:100],
                }

        return outliers_info

    def detect_outliers_iqr(
        self, df: pd.DataFrame, multiplier: float = 1.5, columns: list[str] | None = None
    ) -> dict[str, any]:
        """使用 IQR 检测异常值"""
        target_columns = self._get_numeric_columns(df, columns)
        outliers_info = {"method": "iqr", "multiplier": multiplier, "columns": {}}

        for col in target_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR

            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_indices = df[outlier_mask].index.tolist()

            if outlier_indices:
                outliers_info["columns"][col] = {
                    "outlier_count": len(outlier_indices),
                    "outlier_ratio": len(outlier_indices) / len(df),
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "outlier_indices": outlier_indices[:100],
                }

        return outliers_info

    def _get_iqr_bounds(self, series: pd.Series, multiplier: float) -> tuple[float, float]:
        """获取 IQR 边界"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        return Q1 - multiplier * IQR, Q3 + multiplier * IQR

    def remove_outliers(
        self, df: pd.DataFrame, method: str = "iqr", threshold: float = 1.5, columns: list[str] | None = None
    ) -> pd.DataFrame:
        """移除异常值"""
        df_clean = df.copy()
        target_columns = self._get_numeric_columns(df_clean, columns)

        for col in target_columns:
            if method == "iqr":
                lower, upper = self._get_iqr_bounds(df_clean[col], threshold)
                df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
            elif method == "zscore":
                clean_vals = df_clean[col].dropna()
                z_scores = np.abs(stats.zscore(clean_vals))
                mask = z_scores <= threshold
                valid_indices = clean_vals[mask].index
                df_clean = df_clean.loc[df_clean.index.isin(valid_indices) | df_clean[col].isna()]

        return df_clean

    def cap_outliers(
        self, df: pd.DataFrame, method: str = "iqr", threshold: float = 1.5, columns: list[str] | None = None
    ) -> pd.DataFrame:
        """盖帽处理异常值（Winsorization）"""
        df_clean = df.copy()
        target_columns = self._get_numeric_columns(df_clean, columns)

        for col in target_columns:
            if method == "iqr":
                lower, upper = self._get_iqr_bounds(df_clean[col], threshold)
            else:
                lower = df_clean[col].quantile(0.01)
                upper = df_clean[col].quantile(0.99)

            df_clean[col] = df_clean[col].clip(lower=lower, upper=upper)

        return df_clean

    def normalize_minmax(
        self, df: pd.DataFrame, columns: list[str] | None = None
    ) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
        """Min-Max 标准化到 [0, 1]"""
        df_norm = df.copy()
        target_columns = self._get_numeric_columns(df_norm, columns)
        params = {}

        for col in target_columns:
            min_val = df_norm[col].min()
            max_val = df_norm[col].max()

            if max_val != min_val:
                df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
                params[col] = (min_val, max_val)

        return df_norm, params

    def standardize_zscore(
        self, df: pd.DataFrame, columns: list[str] | None = None
    ) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
        """Z-score 标准化"""
        df_std = df.copy()
        target_columns = self._get_numeric_columns(df_std, columns)
        params = {}

        for col in target_columns:
            mean_val = df_std[col].mean()
            std_val = df_std[col].std()

            if std_val != 0:
                df_std[col] = (df_std[col] - mean_val) / std_val
                params[col] = (mean_val, std_val)

        return df_std, params

    def generate_quality_report(self, df: pd.DataFrame) -> dict[str, any]:
        """生成数据质量报告"""
        report = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing": self.detect_missing(df),
            "outliers_zscore": self.detect_outliers_zscore(df),
            "outliers_iqr": self.detect_outliers_iqr(df),
            "statistics": {},
        }

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            report["statistics"][col] = {
                "count": int(df[col].count()),
                "mean": float(df[col].mean()) if df[col].count() > 0 else None,
                "std": float(df[col].std()) if df[col].count() > 1 else None,
                "min": float(df[col].min()) if df[col].count() > 0 else None,
                "q25": float(df[col].quantile(0.25)) if df[col].count() > 0 else None,
                "median": float(df[col].median()) if df[col].count() > 0 else None,
                "q75": float(df[col].quantile(0.75)) if df[col].count() > 0 else None,
                "max": float(df[col].max()) if df[col].count() > 0 else None,
            }

        return report


# 单例
data_cleaner = DataCleaner()
