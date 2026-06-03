"""
零售门店选址配置
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetailLocationConfig:
    """零售门店选址配置"""

    # 目标变量配置
    target_column: str = "monthly_sales"  # 月均销售额

    # 必填字段
    required_columns: list[str] = field(
        default_factory=lambda: [
            "store_id",
            "store_name",
            "address",
            "latitude",
            "longitude",
            "store_area",
            "monthly_sales",
        ]
    )

    # 特征配置
    feature_config: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            # 基础特征
            "store_area": {"type": "numeric", "required": True},
            # 位置特征
            "distance_to_subway": {"type": "numeric", "required": False},
            "bus_stop_count_500m": {"type": "numeric", "required": False},
            "parking_lot_count": {"type": "numeric", "required": False},
            "is_main_street": {"type": "categorical", "required": False},
            "business_district_type": {"type": "categorical", "required": False},
            # 人口特征
            "population_1km": {"type": "numeric", "required": False},
            "population_2km": {"type": "numeric", "required": False},
            "population_density": {"type": "numeric", "required": False},
            "avg_age": {"type": "numeric", "required": False},
            "young_ratio_18_30": {"type": "numeric", "required": False},
            "avg_income": {"type": "numeric", "required": False},
            # 竞争特征
            "competitor_count_1km": {"type": "numeric", "required": False},
            "competitor_count_2km": {"type": "numeric", "required": False},
            "distance_to_nearest_competitor": {"type": "numeric", "required": False},
            "market_saturation": {"type": "numeric", "required": False},
            # 租金特征
            "rent_per_sqm": {"type": "numeric", "required": False},
            "regional_avg_rent": {"type": "numeric", "required": False},
        }
    )

    # 数据清洗配置
    cleaning_config: dict[str, Any] = field(
        default_factory=lambda: {
            "missing_value_threshold": 0.3,  # 缺失超过30%的列考虑删除
            "outlier_method": "iqr",  # iqr 或 zscore
            "outlier_threshold": 1.5,
            "handle_outliers": "cap",  # remove 或 cap
        }
    )

    # 模型配置
    model_config: dict[str, Any] = field(
        default_factory=lambda: {
            "test_size": 0.2,
            "random_state": 42,
            "cv_folds": 5,
            "models_to_try": ["linear", "random_forest", "xgboost"],
        }
    )

    @classmethod
    def get_default_config(cls) -> "RetailLocationConfig":
        """获取默认配置"""
        return cls()

    def validate_data_columns(self, df_columns: list[str]) -> tuple[bool, list[str]]:
        """
        验证数据列是否满足要求

        Returns:
            (是否通过, 缺失的必填列列表)
        """
        missing_cols = []
        for col in self.required_columns:
            if col not in df_columns:
                missing_cols.append(col)

        return len(missing_cols) == 0, missing_cols
