"""
零售门店特征工程模块
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """特征工程器"""

    def __init__(self, config: Any | None = None):
        self.config = config
        self.categorical_encoders = {}
        self.scalers = {}
        self.feature_names = []
        self.bins = None

    def generate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成衍生特征

        Args:
            df: 原始数据

        Returns:
            增加了衍生特征的数据
        """
        df_out = df.copy()

        # 1. 对数变换（用于长尾分布特征）
        if "population_1km" in df_out.columns:
            df_out["log_population_1km"] = np.log1p(df_out["population_1km"])

        if "avg_income" in df_out.columns:
            df_out["log_avg_income"] = np.log1p(df_out["avg_income"])

        if "distance_to_subway" in df_out.columns:
            df_out["log_distance_to_subway"] = np.log1p(df_out["distance_to_subway"])

        # 2. 组合特征
        if "population_1km" in df_out.columns and "competitor_count_1km" in df_out.columns:
            df_out["population_per_competitor"] = df_out["population_1km"] / (df_out["competitor_count_1km"] + 1)

        if "rent_per_sqm" in df_out.columns and "population_1km" in df_out.columns:
            df_out["rent_to_population_ratio"] = df_out["rent_per_sqm"] / (np.log1p(df_out["population_1km"]))

        # 3. 区间特征
        if "distance_to_subway" in df_out.columns:
            col_name = "subway_proximity"
            if self.bins is None:
                df_out[col_name], self.bins = pd.qcut(
                    df_out["distance_to_subway"], q=4, labels=False, duplicates="drop", retbins=True
                )
            else:
                df_out[col_name] = pd.cut(
                    df_out["distance_to_subway"], bins=self.bins, labels=False, include_lowest=True
                )

        # 4. 交互特征
        if "store_area" in df_out.columns and "population_1km" in df_out.columns:
            df_out["area_population_interaction"] = df_out["store_area"] * np.log1p(df_out["population_1km"])

        logger.info(f"Generated derived features, new shape: {df_out.shape}")
        return df_out

    def encode_categorical_features(
        self,
        df: pd.DataFrame,
        categorical_columns: list[str] | None = None,
        exclude_columns: list[str] | None = None,
        method: str = "onehot",
        fit: bool = True,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        编码分类特征

        Args:
            df: 数据
            categorical_columns: 分类列列表
            exclude_columns: 要排除的列（如ID、名称等唯一标识）
            method: 编码方法 (onehot)
            fit: 是否训练编码器

        Returns:
            (编码后的数据, 编码器字典)
        """
        df_out = df.copy()

        if exclude_columns is None:
            exclude_columns = ["store_id", "store_name", "address"]

        if categorical_columns is None:
            categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # 排除不需要编码的列
        categorical_columns = [col for col in categorical_columns if col not in exclude_columns]

        if method == "onehot":
            for col in categorical_columns:
                if col not in df_out.columns:
                    continue

                if fit:
                    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore", drop="first")
                    encoded = encoder.fit_transform(df_out[[col]])
                    self.categorical_encoders[col] = encoder
                else:
                    if col not in self.categorical_encoders:
                        logger.warning(f"No encoder for column {col}, skipping")
                        continue
                    encoder = self.categorical_encoders[col]
                    encoded = encoder.transform(df_out[[col]])

                # 创建新列名
                categories = encoder.categories_[0][1:]  # drop_first
                new_columns = [f"{col}_{cat}" for cat in categories]

                # 合并到 DataFrame
                encoded_df = pd.DataFrame(encoded, index=df_out.index, columns=new_columns)
                df_out = pd.concat([df_out, encoded_df], axis=1)

                # 删除原始列
                df_out = df_out.drop(col, axis=1)

        return df_out, self.categorical_encoders

    def standardize_numeric_features(
        self, df: pd.DataFrame, numeric_columns: list[str] | None = None, method: str = "standard", fit: bool = True
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        标准化数值特征

        Args:
            df: 数据
            numeric_columns: 数值列列表
            method: 标准化方法 (standard, minmax)
            fit: 是否训练标准化器

        Returns:
            (标准化后的数据, 标准化器字典)
        """
        df_out = df.copy()

        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        # 排除不需要标准化的列
        exclude_cols = []
        if hasattr(self.config, "target_column"):
            exclude_cols.append(self.config.target_column)

        numeric_columns = [col for col in numeric_columns if col not in exclude_cols]

        if method == "standard":
            scaler = StandardScaler()

            if fit:
                scaled_data = scaler.fit_transform(df_out[numeric_columns])
                self.scalers["standard"] = scaler
            else:
                if "standard" not in self.scalers:
                    logger.warning("No standard scaler fitted, skipping standardization")
                    return df_out, self.scalers
                scaler = self.scalers["standard"]
                scaled_data = scaler.transform(df_out[numeric_columns])

            df_out[numeric_columns] = scaled_data

        elif method == "minmax":
            # Min-Max 标准化
            for col in numeric_columns:
                if fit:
                    min_val = df_out[col].min()
                    max_val = df_out[col].max()
                    self.scalers[f"minmax_{col}"] = (min_val, max_val)
                else:
                    if f"minmax_{col}" not in self.scalers:
                        continue
                    min_val, max_val = self.scalers[f"minmax_{col}"]

                if max_val != min_val:
                    df_out[col] = (df_out[col] - min_val) / (max_val - min_val)

        return df_out, self.scalers

    def select_features(
        self, df: pd.DataFrame, target_col: str, method: str = "mutual_info", top_k: int = 20
    ) -> list[str]:
        """
        特征选择

        Args:
            df: 数据
            target_col: 目标列
            method: 选择方法 (mutual_info, correlation)
            top_k: 保留的特征数量

        Returns:
            选中的特征列表
        """
        feature_cols = [col for col in df.columns if col != target_col]
        numeric_features = [col for col in feature_cols if pd.api.types.is_numeric_dtype(df[col])]

        if not numeric_features:
            return numeric_features[:top_k]

        if method == "mutual_info":
            X = df[numeric_features].fillna(0)
            y = df[target_col].fillna(df[target_col].median())
            mi = mutual_info_regression(X, y, random_state=42)
            mi_series = pd.Series(mi, index=numeric_features).sort_values(ascending=False)
            selected_features = mi_series.head(top_k).index.tolist()
            logger.info(f"Selected top {len(selected_features)} features by mutual information")
            return selected_features

        if method == "correlation":
            correlations = []
            for col in numeric_features:
                if df[col].isna().any():
                    continue
                corr = df[col].corr(df[target_col])
                if not np.isnan(corr):
                    correlations.append((col, abs(corr)))

            correlations.sort(key=lambda x: x[1], reverse=True)
            selected_features = [col for col, corr in correlations[:top_k]]

            logger.info(f"Selected top {len(selected_features)} features by correlation")
            return selected_features

        return numeric_features[:top_k]

    def process_features(
        self,
        df: pd.DataFrame,
        target_col: str,
        generate_derived: bool = True,
        encode_categorical: bool = True,
        standardize: bool = True,
        feature_selection: bool = False,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        完整的特征处理流程

        Args:
            df: 原始数据
            target_col: 目标列名
            generate_derived: 是否生成衍生特征
            encode_categorical: 是否编码分类特征
            standardize: 是否标准化
            feature_selection: 是否进行特征选择

        Returns:
            (处理后的数据, 处理元信息)
        """
        df_processed = df.copy()
        meta_info = {}

        # 1. 生成衍生特征
        if generate_derived:
            df_processed = self.generate_derived_features(df_processed)

        # 2. 编码分类特征
        categorical_cols = df_processed.select_dtypes(include=["object", "category"]).columns.tolist()
        categorical_cols = [col for col in categorical_cols if col != target_col]

        if encode_categorical and categorical_cols:
            df_processed, encoders = self.encode_categorical_features(df_processed, categorical_cols)
            meta_info["categorical_encoders"] = encoders

        # 3. 标准化数值特征
        if standardize:
            df_processed, scalers = self.standardize_numeric_features(df_processed)
            meta_info["scalers"] = scalers

        # 4. 特征选择
        if feature_selection:
            selected_features = self.select_features(df_processed, target_col)
            meta_info["selected_features"] = selected_features
            df_processed = df_processed[[target_col] + selected_features]

        self.feature_names = [col for col in df_processed.columns if col != target_col]

        return df_processed, meta_info
