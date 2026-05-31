"""
销售预测配置
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SalesForecastConfig:
    target_column: str = "sales"
    
    required_columns: List[str] = field(default_factory=lambda: [
        "date", "product_id", "category", "sales"
    ])
    
    feature_config: dict = field(default_factory=lambda: {
        "numerical_features": [
            "price", "discount", "inventory", "promotion_budget"
        ],
        "categorical_features": [
            "product_id", "category", "weekday", "month", "is_holiday"
        ],
        "time_features": [
            "day_of_week", "month_of_year", "quarter"
        ]
    })
    
    model_config: dict = field(default_factory=lambda: {
        "model_names": ["linear", "random_forest", "gbm"],
        "test_size": 0.2,
        "random_state": 42
    })
    
    @classmethod
    def get_default_config(cls):
        return cls()
    
    def validate_data_columns(self, data_columns: list):
        missing_columns = [
            col for col in self.required_columns
            if col not in data_columns
        ]
        is_valid = len(missing_columns) == 0
        return is_valid, missing_columns
