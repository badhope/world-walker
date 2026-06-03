"""
销售预测特征工程
"""

import logging

import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)


class SalesFeatureEngineer:
    """销售预测特征工程"""

    def __init__(self, config=None):
        self.config = config
        self.feature_names = []
        self.scaler = None
        self.encoders = {}

    def generate_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成时间特征"""
        df = df.copy()

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df["day_of_week"] = df["date"].dt.dayofweek
            df["weekday"] = df["date"].dt.day_name()
            df["month"] = df["date"].dt.month
            df["month_of_year"] = df["date"].dt.month
            df["quarter"] = df["date"].dt.quarter
            df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        logger.info(f"Generated time features, new shape: {df.shape}")
        return df

    def generate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成衍生特征"""
        df = df.copy()

        # 价格相关特征
        if "price" in df.columns and "discount" in df.columns:
            df["discounted_price"] = df["price"] * (1 - df["discount"])
            df["discount_amount"] = df["price"] * df["discount"]

        # 库存销售比
        if "inventory" in df.columns:
            df["inventory_level"] = pd.qcut(df["inventory"], q=3, labels=["Low", "Medium", "High"], duplicates="drop")

        # 促销强度
        if "promotion_budget" in df.columns:
            df["promotion_intensity"] = pd.qcut(
                df["promotion_budget"], q=4, labels=["None", "Low", "Medium", "High"], duplicates="drop"
            )

        logger.info(f"Generated derived features, new shape: {df.shape}")
        return df

    def encode_categorical_features(
        self, df: pd.DataFrame, categorical_cols: list[str], exclude_columns: list[str] | None = None
    ) -> tuple[pd.DataFrame, dict]:
        """编码分类特征"""
        df = df.copy()

        if exclude_columns is None:
            exclude_columns = []

        categorical_cols = [col for col in categorical_cols if col in df.columns and col not in exclude_columns]

        if not categorical_cols:
            return df, {}

        encoders = {}

        for col in categorical_cols:
            if df[col].nunique() > 50:  # 太多唯一值，频率编码
                freq_map = df[col].value_counts(normalize=True)
                df[f"{col}_freq"] = df[col].map(freq_map)
                df = df.drop(col, axis=1)
                encoders[col] = ("frequency", freq_map)
            else:  # One-Hot 编码
                encoder = OneHotEncoder(sparse_output=False, drop="first", handle_unknown="ignore")
                encoded = encoder.fit_transform(df[[col]].fillna("Missing"))
                encoded_df = pd.DataFrame(
                    encoded, columns=[f"{col}_{cat}" for cat in encoder.get_feature_names_out([col])], index=df.index
                )
                df = pd.concat([df.drop(col, axis=1), encoded_df], axis=1)
                encoders[col] = ("onehot", encoder)

        self.encoders = encoders
        logger.info(f"Encoded {len(categorical_cols)} categorical features")
        return df, encoders

    def scale_numerical_features(self, df: pd.DataFrame, numerical_cols: list[str]) -> pd.DataFrame:
        """标准化数值特征"""
        df = df.copy()

        numerical_cols = [col for col in numerical_cols if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]

        if not numerical_cols:
            return df

        if self.scaler is None:
            self.scaler = StandardScaler()
            df[numerical_cols] = self.scaler.fit_transform(df[numerical_cols].fillna(0))
        else:
            df[numerical_cols] = self.scaler.transform(df[numerical_cols].fillna(0))

        logger.info(f"Scaled {len(numerical_cols)} numerical features")
        return df

    def process_features(
        self,
        df: pd.DataFrame,
        target_col: str,
        generate_derived: bool = True,
        encode_categorical: bool = True,
        standardize: bool = False,
    ) -> tuple[pd.DataFrame, dict]:
        """完整特征处理流程"""
        df = df.copy()
        meta = {}

        # 1. 时间特征
        df = self.generate_time_features(df)

        # 2. 衍生特征
        if generate_derived:
            df = self.generate_derived_features(df)

        # 3. 分类编码 - 包含所有 object 类型的列，包括我们刚生成的分类特征
        if encode_categorical:
            exclude_cols = ["date", "product_id"]
            # 明确列出所有需要编码的分类列
            categorical_cols = []
            # 从 config 获取
            if self.config:
                categorical_cols.extend(self.config.feature_config.get("categorical_features", []))
            # 从数据中获取所有 object 类型的列
            object_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
            categorical_cols.extend([col for col in object_cols if col not in categorical_cols])
            # 去重
            categorical_cols = list(set(categorical_cols))

            df, encoders = self.encode_categorical_features(df, categorical_cols, exclude_columns=exclude_cols)
            meta["encoders"] = encoders

        # 4. 确保没有缺失值
        df = df.fillna(0)

        # 5. 只保留数值列用于模型
        numeric_df = df.select_dtypes(include=["number"])
        # 确保目标列存在
        if target_col in df.columns and target_col not in numeric_df.columns:
            numeric_df[target_col] = df[target_col]

        # 6. 保存特征列表
        feature_cols = [col for col in numeric_df.columns if col != target_col and col != "date"]
        self.feature_names = feature_cols

        return numeric_df, meta
